"""docx 렌더: 스타일·eastAsia 폰트·wordWrap·머리글/바닥글 필드·표 헤더 음영·캡션·마커 형광·목차."""

import zipfile
from pathlib import Path

from docgen.docx_render import render_docx
from docx import Document

FIXTURE = str(Path(__file__).resolve().parents[1] / "fixtures" / "gateway-design.doc.md")


def _render(tmp_path):
    out = tmp_path / "out.docx"
    r = render_docx(FIXTURE, out_path=str(out), base=".")
    return r, out


def _part(z, name):
    return z.read(name).decode("utf-8") if name in z.namelist() else ""


def test_opens_and_structure(tmp_path):
    r, out = _render(tmp_path)
    assert Path(r["out_path"]).is_file()
    assert Path(r["out_path"]).is_absolute()
    d = Document(str(out))  # 복구 프롬프트 없이 열림(파싱 성공)
    assert len(d.tables) >= 3
    names = {s.name for s in d.styles}
    assert {"Code", "TableText", "Caption"} <= names
    assert r["headings"] and r["headings"][0]["text"].startswith("1.")


def test_xml_traps(tmp_path):
    _r, out = _render(tmp_path)
    with zipfile.ZipFile(out) as z:
        doc = _part(z, "word/document.xml")
        styles = _part(z, "word/styles.xml")
        settings = _part(z, "word/settings.xml")
        header = "".join(_part(z, n) for n in z.namelist() if "header" in n)
        footer = "".join(_part(z, n) for n in z.namelist() if "footer" in n)
    assert 'w:eastAsia="맑은 고딕"' in doc or "맑은 고딕" in styles  # 한글 폰트 지정
    assert 'w:wordWrap w:val="0"' in styles  # 어절 줄바꿈
    assert "w:shd" in doc and 'w:fill="F7F7F7"' in doc  # 표 헤더/밴딩 음영
    assert 'w:highlight w:val="yellow"' in doc  # 마커 형광
    assert "TOC" in doc  # 목차 필드
    assert 'w:val="true"' in settings and "updateFields" in settings
    assert "대외비" in header  # 머리글 보안 등급
    assert "PAGE" in footer  # 바닥글 쪽번호 필드
    assert "[표 1]" in doc  # 표 캡션 번호


def test_default_output_path(tmp_path, monkeypatch):
    # out_path 없으면 render_output_dir(docs/_build) 에 filename_pattern 으로 저장
    monkeypatch.chdir(tmp_path)
    (tmp_path / "STYLE.md").write_text(
        '---\nrender_output_dir: build\nfilename_pattern: "{title}"\n---\n', encoding="utf-8"
    )
    r = render_docx(FIXTURE, base=str(tmp_path))
    assert Path(r["out_path"]).parent.name == "build"
    assert Path(r["out_path"]).is_file()
