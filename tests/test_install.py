"""install.py 순수 함수 + end-to-end. PRD 12.1."""

import json

import install

# ─── 순수 함수 ────────────────────────────────────────────────────────────────


def test_merge_settings_preserve_and_dedup():
    existing = json.dumps(
        {
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo hi"}]}
                ]
            }
        }
    )
    out = install.merge_settings(existing, "python")
    s = json.loads(out)
    cmds = [h["command"] for e in s["hooks"]["PreToolUse"] for h in e["hooks"]]
    assert "echo hi" in cmds  # 기존 훅 보존
    assert any("doc_lint.py --pre" in c for c in cmds)
    # 재병합은 중복을 만들지 않는다(실행기 문자열이 달라도 스크립트+모드로 판단)
    out2 = install.merge_settings(out, "py -3")
    s2 = json.loads(out2)
    pre = [
        h
        for e in s2["hooks"]["PreToolUse"]
        for h in e["hooks"]
        if "doc_lint.py --pre" in h["command"]
    ]
    assert len(pre) == 1


def test_merge_settings_no_python():
    out = install.merge_settings(None, "python", include_post=False)
    assert "PostToolUse" not in out and "py_format" not in out
    assert "PreToolUse" in out and "Stop" in out


def test_fill_frontmatter():
    md = "---\norg: 데이타솔루션 기술연구소\ntone_doc: 서술식\ntheme: datasolution\n---\n본문"
    out = install.fill_frontmatter(
        md, {"org": "테스트연구소", "tone_doc": "경어", "theme": "company"}
    )
    assert "org: 테스트연구소" in out
    assert "tone_doc: 경어" in out
    assert "theme: company" in out
    assert install.fill_frontmatter(out, {"org": None}).count("org: 테스트연구소") == 1


def test_append_snippet_idempotent():
    snip = install.CLAUDE_MARKER + "\n- 규약"
    a = install.append_snippet("", snip)
    assert install.CLAUDE_MARKER in a
    assert install.append_snippet(a, snip) == a  # 멱등
    c = install.append_snippet("# 기존\n\n내용", snip)
    assert "# 기존" in c and install.CLAUDE_MARKER in c


def test_remove_snippet():
    snip = install.CLAUDE_MARKER + "\n- 규약1\n- 규약2"
    assert install.remove_snippet(install.append_snippet("", snip)) == ""
    joined = install.append_snippet("# 기존\n\n내용", snip)
    out = install.remove_snippet(joined)
    assert "# 기존" in out and install.CLAUDE_MARKER not in out


def test_merge_mcp_json():
    out = install.merge_mcp_json(None, "https://gl.example.com/")
    s = json.loads(out)
    assert s["mcpServers"]["gitlab"]["url"] == "https://gl.example.com/api/v4/mcp"
    # 기존 서버 보존, gitlab 덮어쓰지 않음
    ex = json.dumps({"mcpServers": {"other": {"type": "stdio"}}})
    s2 = json.loads(install.merge_mcp_json(ex))
    assert "other" in s2["mcpServers"] and "gitlab" in s2["mcpServers"]


def test_gitignore_idempotent():
    g = install.add_gitignore_line("", "docs/_build/")
    assert "docs/_build/" in g
    assert install.add_gitignore_line(g, "docs/_build/").count("docs/_build/") == 1
    g2 = install.add_gitignore_line(".venv/\n", "docs/_build/")
    assert ".venv/" in g2 and "docs/_build/" in g2


def test_detect_python():
    assert install.detect_python(probe=lambda c: (3, 11) if c == ["python3"] else None) == "python3"
    assert install.detect_python(candidates=[["nope"]], probe=lambda c: None) is None
    assert (
        install.detect_python(candidates=[["python"]], probe=lambda c: (3, 7)) is None
    )  # 너무 낮음


# ─── end-to-end (파일 I/O) ────────────────────────────────────────────────────


def test_install_end_to_end(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    rc = install.main(
        [
            "--target",
            str(tmp_path),
            "--org",
            "테스트연구소",
            "--tone",
            "경어",
            "--gitlab-url",
            "https://gl.example.com",
        ]
    )
    assert rc == 0
    assert (tmp_path / "STYLE.md").exists()
    assert (tmp_path / ".claude" / "hooks" / "doc_lint.py").exists()
    assert (tmp_path / ".claude" / "hooks" / "py_format.py").exists()  # Python 프로젝트
    s = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert set(s["hooks"]) == {"PreToolUse", "PostToolUse", "Stop"}
    style = (tmp_path / "STYLE.md").read_text(encoding="utf-8")
    assert "org: 테스트연구소" in style and "tone_doc: 경어" in style
    assert (tmp_path / "docs" / "glossary.md").exists()
    assert (tmp_path / "docs" / "_build").is_dir()
    mcp = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    assert mcp["mcpServers"]["gitlab"]["url"].endswith("/api/v4/mcp")
    assert "docs/_build/" in (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert install.CLAUDE_MARKER in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")


def test_install_no_python_omits_post(tmp_path):
    # pyproject 없음 -> Python 프로젝트 아님
    install.main(["--target", str(tmp_path)])
    assert not (tmp_path / ".claude" / "hooks" / "py_format.py").exists()
    s = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "PostToolUse" not in s["hooks"]


def test_update_preserves_data(tmp_path):
    install.main(["--target", str(tmp_path)])
    (tmp_path / "STYLE.md").write_text("커스텀", encoding="utf-8")
    install.main(["--target", str(tmp_path), "--update"])
    assert (tmp_path / "STYLE.md").read_text(encoding="utf-8") == "커스텀"
    assert (tmp_path / ".claude" / "hooks" / "doc_lint.py").exists()  # 훅은 갱신됨


def test_agents_md_snippet(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    install.main(["--target", str(tmp_path)])
    assert install.CLAUDE_MARKER in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")


def test_uninstall_removes_ours_only(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    install.main(["--target", str(tmp_path)])
    install.main(["--target", str(tmp_path), "--uninstall"])
    assert not (tmp_path / ".claude" / "hooks" / "doc_lint.py").exists()
    assert not (tmp_path / ".claude" / "hooks" / "py_format.py").exists()
    s = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    cmds = [
        h.get("command", "")
        for ev in s.get("hooks", {}).values()
        for e in ev
        for h in e.get("hooks", [])
    ]
    assert not any("doc_lint" in c or "py_format" in c for c in cmds)
    assert install.CLAUDE_MARKER not in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert (tmp_path / "STYLE.md").exists()  # 데이터 보존
    assert (tmp_path / ".mcp.json").exists()
