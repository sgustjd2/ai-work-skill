"""py_format.py: ruff 탐지·대상 판정. 블록 경로 통합 테스트는 M2. PRD 12.1, 7.6."""

import py_format


def test_detect_ruff_none(tmp_path, monkeypatch):
    monkeypatch.setattr(py_format.shutil, "which", lambda name: None)
    assert py_format.detect_ruff(str(tmp_path)) is None


def test_detect_ruff_uv(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 100\n", encoding="utf-8")
    monkeypatch.setattr(py_format.shutil, "which", lambda name: "/bin/" + name)
    got = py_format.detect_ruff(str(tmp_path))
    assert got[:2] == ["uv", "run"] and got[-1] == "ruff"


def test_detect_ruff_path(tmp_path, monkeypatch):
    # 프로젝트에 ruff 선언 없음 + PATH 에 ruff 있음
    monkeypatch.setattr(
        py_format.shutil, "which", lambda name: "/bin/ruff" if name == "ruff" else None
    )
    assert py_format.detect_ruff(str(tmp_path)) == ["ruff"]


def test_is_target(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("x = 1\n", encoding="utf-8")
    assert py_format.is_target(str(f), str(tmp_path))
    assert not py_format.is_target(str(tmp_path / "a.md"), str(tmp_path))  # .py 아님
    assert not py_format.is_target(str(tmp_path / "missing.py"), str(tmp_path))  # 없음
    pb = tmp_path / "x_pb2.py"
    pb.write_text("x = 1\n", encoding="utf-8")
    assert not py_format.is_target(str(pb), str(tmp_path))  # 생성 코드 제외
