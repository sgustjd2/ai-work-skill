"""미리보기: LibreOffice(soffice) 로 PDF→PNG. 없으면 안내만(세션·CI 를 깨지 않는다)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_SOFFICE_CANDS = [
    "soffice",
    r"C:/Program Files/LibreOffice/program/soffice.exe",
    r"C:/Program Files (x86)/LibreOffice/program/soffice.exe",
    "/usr/bin/soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
]


def _find_soffice() -> str | None:
    env = os.environ.get("SOFFICE_PATH")
    if env and Path(env).exists():
        return env
    which = shutil.which("soffice")
    if which:
        return which
    for c in _SOFFICE_CANDS:
        if Path(c).exists():
            return c
    return None


def _parse_pages(pages: str, total: int) -> list[int]:
    out: list[int] = []
    for part in str(pages).split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out += list(range(int(a), int(b) + 1))
        elif part.isdigit():
            out.append(int(part))
    return [p for p in out if 1 <= p <= total] or list(range(1, min(total, 3) + 1))


def preview(path: str, pages: str = "1-3", dpi: int = 110) -> dict:
    src = Path(path)
    if not src.exists():
        return {"available": False, "images": [], "hint": f"파일 없음: {src}", "warnings": []}
    soffice = _find_soffice()
    if not soffice:
        return {
            "available": False,
            "images": [],
            "hint": "LibreOffice(soffice)가 없어 미리보기를 건너뜁니다. "
            "설치하거나 SOFFICE_PATH 를 설정하세요. 구조 검증은 XML 로 대신합니다.",
            "warnings": [],
        }
    tmp = Path(tempfile.mkdtemp(prefix="docgen_preview_"))
    warnings: list[str] = []
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(src)],
            check=True,
            capture_output=True,
            timeout=120,
        )
        pdf = tmp / (src.stem + ".pdf")
        if not pdf.exists():
            return {"available": False, "images": [], "hint": "PDF 변환 실패", "warnings": warnings}
        images = _pdf_to_png(pdf, tmp, pages, dpi, warnings)
        return {
            "available": True,
            "images": [str(p) for p in images],
            "hint": "",
            "warnings": warnings,
        }
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        return {"available": False, "images": [], "hint": f"변환 오류: {e}", "warnings": warnings}


def _pdf_to_png(pdf: Path, tmp: Path, pages: str, dpi: int, warnings: list) -> list[Path]:
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        subprocess.run(
            [pdftoppm, "-png", "-r", str(dpi), str(pdf), str(tmp / "page")],
            check=True,
            capture_output=True,
            timeout=120,
        )
        out = sorted(tmp.glob("page-*.png"))
        page_nums = _parse_pages(pages, len(out) or 1)
        return [p for i, p in enumerate(out, start=1) if i in page_nums]
    # pdftoppm 없으면 pypdfium/Pillow 없이 soffice png(첫 장만)
    warnings.append("pdftoppm 이 없어 첫 페이지만 PNG 로 변환합니다.")
    soffice = _find_soffice()
    subprocess.run(
        [soffice, "--headless", "--convert-to", "png", "--outdir", str(tmp), str(pdf)],
        check=True,
        capture_output=True,
        timeout=120,
    )
    return sorted(tmp.glob("*.png"))
