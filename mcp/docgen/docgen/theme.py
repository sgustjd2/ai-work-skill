"""테마 로딩과 색 조회. 원색·폰트·치수는 themes/*.json 에만 있다(소스에 hex 리터럴 없음).

해석 순서(이름/경로 → 실제 파일):
  1. 경로처럼 보이면(구분자 또는 .json) 그 파일을 base_dir 기준으로 연다.
  2. 이름이 있으면 [base_dir/docs, DOCGEN_THEME_DIR, 플러그인 themes] 에서 <이름>.json.
  3. 이름이 없으면 base_dir/docs/theme.json → 플러그인 themes/datasolution.json.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

REQUIRED_TOP = ("name", "colors", "fonts", "docx", "pptx")
REQUIRED_COLORS = (
    "primary",
    "accent",
    "action",
    "ink",
    "ink_muted",
    "ink_subtle",
    "line",
    "surface",
    "white",
    "positive",
    "warning",
    "critical",
)


def _repo_root() -> Path:
    env = os.environ.get("AI_WORK_SKILL_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    try:
        cand = here.parents[3]
        if (cand / "themes").exists():
            return cand
    except IndexError:
        pass
    return Path.cwd()


def _plugin_themes() -> Path:
    return _repo_root() / "themes"


def _validate(data: dict, src: str) -> None:
    missing = [k for k in REQUIRED_TOP if k not in data]
    if missing:
        raise ValueError(f"테마 {src}: 필수 키 누락 {missing}")
    cmiss = [k for k in REQUIRED_COLORS if k not in data.get("colors", {})]
    if cmiss:
        raise ValueError(f"테마 {src}: colors 필수 역할 누락 {cmiss}")


@lru_cache(maxsize=16)
def _read(path_str: str) -> dict:
    path = Path(path_str)
    data = json.loads(path.read_text(encoding="utf-8"))
    _validate(data, path.name)
    return data


def _looks_like_path(name: str) -> bool:
    return ("/" in name) or ("\\" in name) or name.endswith(".json")


def load_theme(name: str | None = None, base_dir: str | Path | None = None) -> dict:
    base = Path(base_dir).resolve() if base_dir else None

    if name and _looks_like_path(name):
        p = Path(name)
        if not p.is_absolute() and base:
            p = base / p
        if p.exists():
            return _read(str(p.resolve()))
        raise FileNotFoundError(f"테마 파일 없음: {p}")

    dirs: list[Path] = []
    if base:
        dirs.append(base / "docs")
    env_dir = os.environ.get("DOCGEN_THEME_DIR")
    if env_dir:
        dirs.append(Path(env_dir))
    dirs.append(_plugin_themes())

    candidates: list[Path] = []
    if name:
        for d in dirs:
            candidates.append(d / f"{name}.json")
    else:
        if base:
            candidates.append(base / "docs" / "theme.json")
        candidates.append(_plugin_themes() / "datasolution.json")

    for c in candidates:
        if c.exists():
            return _read(str(c.resolve()))
    raise FileNotFoundError(
        f"테마를 찾을 수 없습니다(name={name!r}). 확인한 경로: "
        + ", ".join(str(c) for c in candidates)
    )


# ─── 색 조회 ───────────────────────────────────────────────────────────────
def color(theme: dict, role: str, fallback: str | None = None) -> str:
    """역할 이름 → hex 문자열('#RRGGBB'). 없으면 fallback 역할, 그것도 없으면 ink."""
    colors = theme.get("colors", {})
    if role in colors:
        return colors[role]
    if fallback and fallback in colors:
        return colors[fallback]
    return colors.get("ink", colors.get("primary"))


def rgb_tuple(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_hex(theme: dict, role: str, fallback: str | None = None) -> str:
    """python-docx/pptx RGBColor.from_string 용 6자리 hex(# 없이)."""
    return color(theme, role, fallback).lstrip("#").upper()


def mix(hex_a: str, hex_b: str, t: float) -> str:
    """hex_a 와 hex_b 를 t(0~1) 비율로 섞은 hex('#RRGGBB'). t=0 → a, t=1 → b."""
    ra, ga, ba = rgb_tuple(hex_a)
    rb, gb, bb = rgb_tuple(hex_b)
    r = round(ra + (rb - ra) * t)
    g = round(ga + (gb - ga) * t)
    b = round(ba + (bb - ba) * t)
    return f"#{r:02X}{g:02X}{b:02X}"


def tint(theme: dict, role: str, t: float) -> str:
    """역할 색을 white 쪽으로 t 만큼 흐리게(구성도 llm 노드 배경 등)."""
    return mix(color(theme, role), color(theme, "white"), t)


def relative_luminance(hex_str: str) -> float:
    def chan(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = rgb_tuple(hex_str)
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    la, lb = relative_luminance(hex_a), relative_luminance(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def font(theme: dict, key: str) -> str:
    return theme.get("fonts", {}).get(key, "")


def font_paths(theme: dict) -> list[str]:
    return list(theme.get("fonts", {}).get("font_paths", []))
