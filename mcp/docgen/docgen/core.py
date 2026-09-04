"""공통: 기준 디렉터리·STYLE.md 로드·출력 경로·테마 해석. 렌더러가 공유한다."""

from __future__ import annotations

import os
import re
from datetime import date as _date
from pathlib import Path

from .lint import doc_lint  # lint 모듈이 templates/ 를 sys.path 에 넣고 doc_lint 를 노출한다

RENDER_DEFAULTS = {
    "filename_pattern": "{title}_v{version}_{date:%Y%m%d}",
    "render_output_dir": "docs/_build",
    "office_font": "맑은 고딕",
    "org": "",
    "author": "",
    "tone_doc": "서술식",
    "template_docx": None,
    "template_pptx": None,
    "theme": None,
    "security": None,
    "placeholder_marker": "[확인 필요]",
}


def base_dir(explicit=None):
    return explicit or os.environ.get("DOCGEN_PROJECT_DIR") or os.getcwd()


def load_style(bdir):
    cfg = doc_lint.load_config(bdir) or {}
    merged = dict(RENDER_DEFAULTS)
    merged.update({k: v for k, v in cfg.items() if v is not None and v != "null"})
    return merged


def safe_name(name):
    name = re.sub(r'[<>:"/\\|?*]', "", str(name)).strip()
    return re.sub(r"\s+", "_", name) or "document"


def _to_date(v):
    if isinstance(v, _date):
        return v
    try:
        return _date.fromisoformat(str(v))
    except Exception:
        return _date.today()


def out_path_for(spec_path, fm, style, out_path, ext, bdir):
    if out_path:
        p = Path(out_path)
        return p if p.is_absolute() else Path(bdir) / p
    pattern = style.get("filename_pattern") or RENDER_DEFAULTS["filename_pattern"]
    title = safe_name(fm.get("title") or Path(spec_path).stem)
    try:
        name = pattern.format(
            title=title,
            version=fm.get("version", "0.1"),
            date=_to_date(fm.get("date")),
            org=style.get("org", ""),
        )
    except Exception:
        name = title
    outdir = Path(bdir) / (style.get("render_output_dir") or RENDER_DEFAULTS["render_output_dir"])
    return outdir / (safe_name(name) + ext)


def theme_name(fm, style, explicit):
    return explicit or fm.get("theme") or style.get("theme")


def marker_pattern(_style):
    """placeholder_marker 어휘를 형광 강조 정규식으로. [확인 필요]·[금액 입력 필요] 등."""
    # ponytail: 기본 마커 어휘만. 넓히려면 STYLE.md 값을 여기 반영.
    return re.compile(r"\[[^\]]*(?:확인|입력|미정|TBD)[^\]]*\]")
