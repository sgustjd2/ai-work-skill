"""config.yaml 검증(V1~V8)과 diff. 로컬 파일만 본다(네트워크 없음).

규칙은 PRD §9.1. 배포 전에 폴백 참조 무결성·인라인 시크릿·환경변수 참조 존재를 잡는다.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .core import KNOWN_PROVIDERS, ROUTING_STRATEGIES

SENSITIVE = (
    "api_key",
    "aws_secret_access_key",
    "aws_access_key_id",
    "vertex_credentials",
    "master_key",
    "database_url",
    "api_base",
)
_SECRET = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|glpat-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}"
    r"|AIza[0-9A-Za-z_-]{35}|-----BEGIN"
)
_PLACEHOLDER = re.compile(r"(.)\1{5,}|changeme|your[_-]|example|placeholder|<[^>]*>", re.I)
_TOKENISH = re.compile(r"^[A-Za-z0-9_\-]{20,}$")


def _finding(code, level, path, message):
    return {"code": code, "level": level, "path": path, "message": message}


def _looks_secret(val: str) -> bool:
    s = str(val)
    if _PLACEHOLDER.search(s):
        return False
    if _SECRET.search(s):
        return True
    # postgres://user:pass@host 처럼 자격증명이 박힌 URL
    if "://" in s and "@" in s and re.search(r"://[^:/@]+:[^@/]+@", s):
        return True
    return _TOKENISH.match(s) is not None and not s.startswith("os.environ/")


def _env_names_from_example(config_path: Path) -> set[str]:
    for name in (".env.example", ".env"):
        p = config_path.parent / name
        if p.exists():
            out = set()
            for line in p.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=", line.strip())
                if m:
                    out.add(m.group(1))
            return out
    return set()


def config_validate(path: str) -> dict:
    p = Path(path)
    findings: list[dict] = []
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as e:
        return {"ok": False, "findings": [_finding("V1", "error", str(p), f"YAML 파싱 실패: {e}")]}
    if not isinstance(data, dict):
        return {
            "ok": False,
            "findings": [_finding("V1", "error", str(p), "최상위가 매핑이 아닙니다.")],
        }

    model_list = data.get("model_list") or []
    if not model_list:
        findings.append(_finding("V2", "error", "model_list", "model_list 가 비어 있습니다."))

    model_names: set[str] = set()
    seen: dict[tuple, int] = {}
    import os

    env_names = _env_names_from_example(p)

    for i, item in enumerate(model_list):
        base = f"model_list[{i}]"
        if not isinstance(item, dict):
            findings.append(_finding("V2", "error", base, "항목이 매핑이 아닙니다."))
            continue
        name = item.get("model_name")
        lp = item.get("litellm_params") or {}
        model = lp.get("model")
        if not name or not model:
            findings.append(
                _finding("V2", "error", base, "model_name 또는 litellm_params.model 이 없습니다.")
            )
            continue
        model_names.add(name)
        if not any(str(model).startswith(pre) for pre in KNOWN_PROVIDERS):
            findings.append(
                _finding(
                    "V3",
                    "warn",
                    f"{base}.litellm_params.model",
                    f"알 수 없는 제공자 접두사: {model}",
                )
            )
        for field in SENSITIVE:
            val = lp.get(field) if field in lp else data.get("general_settings", {}).get(field)
            if isinstance(val, str) and not val.startswith("os.environ/"):
                if field != "api_base" and _looks_secret(val):
                    findings.append(
                        _finding(
                            "V4",
                            "error",
                            f"{base}.litellm_params.{field}",
                            "시크릿이 인라인되어 있습니다. os.environ/ 참조로 바꾸세요.",
                        )
                    )
            if isinstance(val, str) and val.startswith("os.environ/"):
                env = val.split("/", 1)[1]
                if env not in os.environ and env not in env_names:
                    findings.append(
                        _finding(
                            "V5",
                            "warn",
                            f"{base}.litellm_params.{field}",
                            f"환경변수 {env} 가 프로세스에도 .env.example 에도 없습니다.",
                        )
                    )
        key = (name, model, lp.get("api_base"))
        seen[key] = seen.get(key, 0) + 1

    # general_settings 시크릿·마스터키
    gs = data.get("general_settings", {}) or {}
    for field in ("master_key", "database_url"):
        val = gs.get(field)
        if isinstance(val, str) and not val.startswith("os.environ/") and _looks_secret(val):
            findings.append(
                _finding(
                    "V4",
                    "error",
                    f"general_settings.{field}",
                    "시크릿이 인라인되어 있습니다. os.environ/ 참조로.",
                )
            )
    if not gs.get("master_key"):
        findings.append(
            _finding(
                "V8",
                "warn",
                "general_settings.master_key",
                "master_key 가 없습니다. admin API 가 열려 있을 수 있습니다.",
            )
        )
    if "background_health_checks" not in gs:
        findings.append(
            _finding(
                "V8",
                "warn",
                "general_settings.background_health_checks",
                "background_health_checks 가 설정되지 않았습니다.",
            )
        )

    # 폴백 참조 무결성
    alias = set((data.get("router_settings", {}) or {}).get("model_group_alias", {}) or {})
    valid_targets = model_names | alias
    ls = data.get("litellm_settings", {}) or {}
    for fb_key in ("fallbacks", "context_window_fallbacks"):
        for entry in ls.get(fb_key, []) or []:
            if not isinstance(entry, dict):
                continue
            for src, dsts in entry.items():
                if src not in valid_targets:
                    findings.append(
                        _finding(
                            "V6",
                            "error",
                            f"litellm_settings.{fb_key}",
                            f"폴백 출발 '{src}' 가 model_list 에 없습니다.",
                        )
                    )
                for d in dsts if isinstance(dsts, list) else [dsts]:
                    if d not in valid_targets:
                        findings.append(
                            _finding(
                                "V6",
                                "error",
                                f"litellm_settings.{fb_key}",
                                f"폴백 대상 '{d}' 가 model_list 에 없습니다.",
                            )
                        )

    rs = (data.get("router_settings", {}) or {}).get("routing_strategy")
    if rs and rs not in ROUTING_STRATEGIES:
        findings.append(
            _finding(
                "V7",
                "warn",
                "router_settings.routing_strategy",
                f"알 수 없는 routing_strategy: {rs}",
            )
        )

    for key, n in seen.items():
        if n > 1:
            findings.append(
                _finding(
                    "V8",
                    "warn",
                    "model_list",
                    f"중복 배포(무의미): model_name={key[0]}, model={key[1]}, api_base={key[2]}",
                )
            )

    ok = not any(f["level"] == "error" for f in findings)
    return {"ok": ok, "findings": findings, "path": str(p.resolve())}


def config_diff(path_a: str, path_b: str) -> dict:
    def load(p):
        return yaml.safe_load(Path(p).read_text(encoding="utf-8")) or {}

    a, b = load(path_a), load(path_b)

    def models(d):
        out = {}
        for it in d.get("model_list", []) or []:
            lp = it.get("litellm_params", {}) or {}
            out[(it.get("model_name"), lp.get("model"), lp.get("api_base"))] = it
        return out

    ma, mb = models(a), models(b)
    added = [f"{k[0]} ({k[1]})" for k in mb.keys() - ma.keys()]
    removed = [f"{k[0]} ({k[1]})" for k in ma.keys() - mb.keys()]
    changed = []
    for section in ("litellm_settings", "router_settings", "general_settings"):
        if a.get(section) != b.get(section):
            changed.append({"path": section, "a": a.get(section), "b": b.get(section)})
    return {"added": sorted(added), "removed": sorted(removed), "changed": changed}
