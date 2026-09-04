#!/usr/bin/env python3
"""scaffold.py — FastAPI 서비스 골격 생성 (FR-20). 표준 라이브러리만.

assets/service/ 를 대상에 복사하며 __pkg__ 디렉터리와 {{pkg}}/{{PKG}}/{{service_title}} 토큰을
치환하고, 옵션에 없는 모듈을 지운다. pyproject·compose·.env.example·README 는 옵션에 맞게 생성한다.

  python scaffold.py --name <pkg> --target <dir> [--title "요약 API"]
      [--with-db|redis|sse|auth|rag|jobs|otel] [--force]

--with-rag 는 --with-db 를 함의하고 compose 의 postgres 이미지를 pgvector 로 바꾼다.
옵션 파일은 첫 줄 `# scaffold: <flag>...` 주석으로 표시되고, 켜진 플래그가 있으면 유지된다.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "service"
MARKER = re.compile(r"^#\s*scaffold:\s*(.+?)\s*$")
FLAGS = ["with-db", "with-redis", "with-sse", "with-auth", "with-rag", "with-jobs", "with-otel"]
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".yaml",
    ".yml",
    ".cfg",
    ".ini",
    ".env",
    ".example",
    ".gitignore",
    "",
}


def enabled_flags(opts: dict) -> set[str]:
    on = {f for f in FLAGS if opts.get(f.replace("-", "_"))}
    if "with-rag" in on:
        on.add("with-db")  # rag 는 db 를 함의
    return on


def render(text: str, pkg: str, title: str) -> str:
    return (
        text.replace("{{pkg}}", pkg)
        .replace("{{PKG}}", pkg.upper())
        .replace("{{service_title}}", title)
    )


def _marker_flags(text: str) -> set[str] | None:
    first = text.splitlines()[0] if text else ""
    m = MARKER.match(first)
    if not m:
        return None
    return {t.strip() for t in m.group(1).split()}


def _strip_marker(text: str) -> str:
    lines = text.splitlines(keepends=True)
    return "".join(lines[1:]) if lines and MARKER.match(lines[0].rstrip("\n")) else text


def _map_path(rel: Path, pkg: str) -> Path:
    return Path(*[pkg if p == "__pkg__" else p for p in rel.parts])


def plan(assets: Path, on: set[str], pkg: str) -> list[tuple[Path, Path, bool]]:
    """(source, target_rel, is_optional_kept). 옵션에 안 맞으면 제외."""
    out = []
    for src in sorted(assets.rglob("*")):
        if src.is_dir() or "__pycache__" in src.parts:
            continue
        rel = src.relative_to(assets)
        text = (
            src.read_text(encoding="utf-8")
            if src.suffix in TEXT_SUFFIXES or src.name.startswith(".")
            else None
        )
        flags = _marker_flags(text) if text is not None else None
        if flags is not None and not (flags & on):
            continue  # 옵션 꺼짐 → 제외
        out.append((src, _map_path(rel, pkg), flags is not None))
    return out


# ─── 생성되는 설정 파일 ──────────────────────────────────────────────────────
def pyproject_text(pkg: str, title: str, on: set[str]) -> str:
    deps = [
        '"fastapi>=0.115,<1"',
        '"uvicorn[standard]>=0.30"',
        '"pydantic-settings>=2.4,<3"',
        '"httpx>=0.27,<1"',
    ]
    if "with-db" in on:
        deps += ['"sqlalchemy[asyncio]>=2.0,<3"', '"asyncpg>=0.29"']
    if "with-redis" in on:
        deps += ['"redis>=5,<6"']
    if "with-otel" in on:
        deps += [
            '"opentelemetry-sdk>=1.27"',
            '"opentelemetry-instrumentation-fastapi>=0.48b0"',
            '"opentelemetry-instrumentation-httpx>=0.48b0"',
            '"opentelemetry-exporter-otlp>=1.27"',
        ]
    dev = ['"pytest>=8,<9"', '"pytest-cov>=5"', '"anyio>=4"', '"respx>=0.21"', '"ruff>=0.6"']
    dep_block = ",\n    ".join(deps)
    dev_block = ",\n    ".join(dev)
    return f"""[project]
name = "{pkg}"
version = "0.1.0"
description = "{title}"
requires-python = ">=3.11"
dependencies = [
    {dep_block},
]

[dependency-groups]
dev = [
    {dev_block},
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "ASYNC"]

[tool.pytest.ini_options]
addopts = "-q --strict-markers"
markers = [
    "anyio: 비동기 테스트",
    "live_llm: 실제 게이트웨이 호출(기본 제외)",
]

[tool.ai-work]
layers = ["api", "services", "infra"]
"""


def compose_text(pkg: str, on: set[str]) -> str:
    pg_image = "pgvector/pgvector:pg16" if "with-rag" in on else "postgres:16"
    parts = [
        "services:",
        "  app:",
        "    build: .",
        '    ports: ["8000:8000"]',
        "    env_file: .env",
        "    depends_on: [litellm]",
        "  litellm:",
        "    image: ghcr.io/berriai/litellm:main-latest",
        '    ports: ["4000:4000"]',
        '    command: ["--config", "/app/config.yaml"]',
    ]
    if "with-db" in on:
        parts += [
            "  postgres:",
            f"    image: {pg_image}",
            "    environment: { POSTGRES_USER: app, POSTGRES_PASSWORD: app, POSTGRES_DB: app }",
            '    ports: ["5432:5432"]',
        ]
    if "with-redis" in on:
        parts += ["  redis:", "    image: redis:7", '    ports: ["6379:6379"]']
    return "\n".join(parts) + "\n"


def env_text(on: set[str]) -> str:
    lines = [
        "APP_ENV=local",
        "APP_LOG_LEVEL=INFO",
        "APP_LLM_BASE_URL=http://localhost:4000",
        "APP_LLM_API_KEY=changeme",
        "APP_LLM_DEFAULT_MODEL=gpt-4o",
        "APP_REQUEST_TIMEOUT_S=30",
    ]
    if "with-db" in on:
        lines.append("APP_DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/app")
    if "with-redis" in on:
        lines.append("APP_REDIS_URL=redis://localhost:6379/0")
    if "with-auth" in on:
        lines.append("APP_API_KEYS=changeme")
    if "with-otel" in on:
        lines.append("OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318")
    return "\n".join(lines) + "\n"


def readme_text(pkg: str, title: str, on: set[str]) -> str:
    extra = ""
    if "with-rag" in on:
        extra = (
            "\nRAG: `POST /api/v1/rag/ingest` 로 문서를 넣고 `POST /api/v1/rag/ask` 로 질의한다.\n"
        )
    return f"""# {title}

LiteLLM 게이트웨이 경유 FastAPI 서비스.

```
uv sync
cp .env.example .env    # 값 채우기
uv run uvicorn {pkg}.main:app --reload
uv run pytest
```

Docker: `docker build -t {pkg} .`
{extra}"""


# ─── IO ──────────────────────────────────────────────────────────────────────
def scaffold(name: str, target: str, title: str | None, opts: dict, force: bool = False) -> dict:
    if not ASSETS.exists():
        raise FileNotFoundError(f"자산을 찾을 수 없습니다: {ASSETS}")
    pkg = name
    title = title or f"{name} service"
    on = enabled_flags(opts)
    dst_root = Path(target).resolve()
    dst_root.mkdir(parents=True, exist_ok=True)

    written, skipped = [], []
    for src, rel, _opt in plan(ASSETS, on, pkg):
        dst = dst_root / rel
        if dst.exists() and not force:
            skipped.append(str(rel))
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in TEXT_SUFFIXES or src.name.startswith("."):
            text = _strip_marker(src.read_text(encoding="utf-8"))
            dst.write_text(render(text, pkg, title), encoding="utf-8")
        else:
            dst.write_bytes(src.read_bytes())
        written.append(str(rel))

    # 생성 파일
    for rel, content in [
        ("pyproject.toml", pyproject_text(pkg, title, on)),
        ("compose.yaml", compose_text(pkg, on)),
        (".env.example", env_text(on)),
        ("README.md", readme_text(pkg, title, on)),
    ]:
        dst = dst_root / rel
        if dst.exists() and not force:
            skipped.append(rel)
            continue
        dst.write_text(content, encoding="utf-8")
        written.append(rel)

    return {
        "package": pkg,
        "target": str(dst_root),
        "flags": sorted(on),
        "written": sorted(written),
        "skipped": sorted(skipped),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="FastAPI 서비스 골격 생성")
    ap.add_argument("--name", required=True)
    ap.add_argument("--target", default=".")
    ap.add_argument("--title", default=None)
    for f in FLAGS:
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    opts = {f.replace("-", "_"): getattr(a, f.replace("-", "_")) for f in FLAGS}
    try:
        r = scaffold(a.name, a.target, a.title, opts, a.force)
    except FileNotFoundError as e:
        sys.stderr.write(f"[scaffold] {e}\n")
        return 1
    if a.json:
        import json

        sys.stdout.write(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    else:
        sys.stdout.write(
            f"[scaffold] {r['package']} 생성 · 플래그 {r['flags'] or '없음'} · "
            f"파일 {len(r['written'])}개 (건너뜀 {len(r['skipped'])})\n"
        )
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
