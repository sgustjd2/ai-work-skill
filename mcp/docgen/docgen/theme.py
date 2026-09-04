"""테마 로드와 색 역할 해석. 색·폰트·치수의 원본은 테마 JSON 뿐이다(렌더러에 hex 리터럴 금지)."""

from __future__ import annotations

import json
import os
from pathlib import Path

# mcp/docgen/docgen/theme.py -> parents[3] = 저장소(또는 플러그인) 루트
PLUGIN_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_THEMES = PLUGIN_ROOT / "themes"


def resolve_theme_path(name, base_dir):
    """테마 이름/경로 -> JSON 파일. 순서: 경로 -> docs -> DOCGEN_THEME_DIR -> themes."""
    base = Path(base_dir)
    if name:
        p = Path(name)
        for cand in (p, base / p):
            if cand.suffix == ".json" and cand.is_file():
                return cand.resolve()
    stem = name or "datasolution"
    search = [base / "docs"]
    env_dir = os.environ.get("DOCGEN_THEME_DIR")
    if env_dir:
        search.append(Path(env_dir))
    search.append(PLUGIN_THEMES)
    for d in search:
        for cand in (d / f"{stem}.json", d / "theme.json"):
            if cand.is_file():
                return cand.resolve()
    return (PLUGIN_THEMES / "datasolution.json").resolve()


def load_theme(name=None, base_dir="."):
    path = resolve_theme_path(name, base_dir)
    theme = json.loads(path.read_text(encoding="utf-8"))
    theme["_path"] = str(path)
    return theme


def color(theme, role):
    """역할 이름(primary 등) 또는 hex 를 hex 로. colors 에 없는 값은 그대로 돌려준다(hex 통과)."""
    colors = theme.get("colors", {})
    if role in colors:
        return colors[role]
    return role  # 이미 hex 이거나 알 수 없는 값


def rgb_tuple(hexstr):
    """#RRGGBB -> (r, g, b)."""
    h = hexstr.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def tint(hexstr, ratio):
    """색을 흰색 쪽으로 섞는다. ratio 는 색의 비율(0.12 = 색 12% + 흰 88%)."""
    r, g, b = rgb_tuple(hexstr)

    def m(v):
        return round(v * ratio + 255 * (1 - ratio))

    return f"#{m(r):02X}{m(g):02X}{m(b):02X}"
