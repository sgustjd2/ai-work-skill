"""프롬프트 파일 로더. 프롬프트는 코드에 인라인하지 않고 prompts/*.md 에 둔다.

각 파일 frontmatter: name, version, model_hint, variables. 본문은 string.Template($var).
기동 시 전부 로드·검증한다. 변수 누락은 렌더 시점에 오류를 낸다.
"""
from __future__ import annotations

import re
from pathlib import Path
from string import Template

_FM = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.S)
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class Prompt:
    def __init__(self, name: str, version: str, variables: list[str], body: str, model_hint: str = ""):
        self.name = name
        self.version = version
        self.variables = variables
        self.model_hint = model_hint
        self._template = Template(body)

    def render(self, **kwargs: str) -> str:
        missing = [v for v in self.variables if v not in kwargs]
        if missing:
            raise KeyError(f"프롬프트 '{self.name}' 변수 누락: {missing}")
        return self._template.substitute(**kwargs)


def _parse(text: str) -> tuple[dict, str]:
    m = _FM.match(text)
    if not m:
        return {}, text
    meta: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                v = [s.strip() for s in v[1:-1].split(",") if s.strip()]
            meta[k.strip()] = v
    return meta, text[m.end():]


def load_prompts(directory: Path | None = None) -> dict[str, Prompt]:
    d = directory or _PROMPTS_DIR
    out: dict[str, Prompt] = {}
    for f in sorted(d.glob("*.md")):
        meta, body = _parse(f.read_text(encoding="utf-8"))
        name = meta.get("name", f.stem)
        out[name] = Prompt(
            name=name,
            version=str(meta.get("version", "1")),
            variables=meta.get("variables", []) if isinstance(meta.get("variables"), list) else [],
            body=body.strip(),
            model_hint=meta.get("model_hint", ""),
        )
    return out
