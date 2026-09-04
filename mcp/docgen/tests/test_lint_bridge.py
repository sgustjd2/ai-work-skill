"""FR-14: docgen.lint 이 templates/doc_lint.py 의 lint() 를 그대로 쓴다(단일 구현)."""

import docgen.lint as dl


def test_single_implementation():
    # docgen.lint import 가 templates/ 를 sys.path 에 넣은 뒤라야 doc_lint 를 import 할 수 있다
    import doc_lint

    assert dl.lint is doc_lint.lint


def test_lint_doc_finds_hard(tmp_path):
    f = tmp_path / "x.md"
    f.write_text("범위 1—2 사이", encoding="utf-8")
    r = dl.lint_doc(str(f), base_dir=str(tmp_path))
    assert any(x["code"] == "H1" for x in r["hard"])
    assert r["warnings"] == []
    assert r["path"].endswith("x.md")


def test_lint_doc_clean(tmp_path):
    f = tmp_path / "y.md"
    f.write_text("범위 1~2 사이", encoding="utf-8")
    r = dl.lint_doc(str(f), base_dir=str(tmp_path))
    assert r["hard"] == []
