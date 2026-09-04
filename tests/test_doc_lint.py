"""doc_lint 룰별 양성/음성 + 예외 + CLI 3모드. PRD 12.1."""

import json
import os
import subprocess
import sys
from pathlib import Path

import doc_lint as d
import pytest

HOOK = Path(d.__file__)


def codes(text, path="a.md", cfg=None, soft=True):
    return {f["code"] for f in d.lint(text, path, cfg, soft=soft)}


def names(text, path="a.md", cfg=None, soft=True):
    return {f["name"] for f in d.lint(text, path, cfg, soft=soft)}


# ─── 하드 룰 H1~H10 (각 양성 2 · 음성 2) ──────────────────────────────────────


def test_h1_dash():
    assert "H1" in codes("범위 1—2 사이")
    assert "H1" in codes("구분 – 항목")
    assert "H1" not in codes("범위 1~2 사이")  # 물결표는 정상
    assert "H1" not in codes("```\n1 — 2\n```")  # 코드 펜스


def test_h2_buzzword_ko():
    assert "H2" in codes("혁신적 서비스를 만든다")
    assert "H2" in codes("팀 간 시너지를 낸다")
    assert "H2" not in codes("요약 API 를 만든다")
    assert "H2" not in codes("`혁신적` 은 금지어다")  # 인라인 코드


def test_h3_buzzword_en():
    assert "H3" in codes("we leverage the gateway")
    assert "H3" in codes("a seamless experience")
    assert "H3" not in codes("we use the gateway")
    assert "H3" not in codes("see https://leverage.example.com/x")  # URL 스킵


def test_h4_ai_phrase_ko():
    assert "H4" in codes("이번 글에서 살펴보겠습니다")
    assert "H4" in codes("다음과 같은 이점이 있습니다")
    assert "H4" not in codes("게이트웨이를 도입한다")
    assert "H4" not in codes("```\n살펴보겠습니다\n```")


def test_h5_ai_phrase_en():
    assert "H5" in codes("In conclusion, we ship it")
    assert "H5" in codes("Let's dive into the config")
    assert "H5" not in codes("We ship the config")
    assert "H5" not in codes("`i hope this helps` 는 금지")


def test_h6_emoji():
    assert "H6" in codes("배포 완료 \U0001f680")
    assert "H6" in codes("좋아요 \U0001f44d")
    assert "H6" not in codes("강조 ★ 항목 ☞ 참고 ☑ 완료")  # 한국 관용 기호
    assert "H6" not in codes("상태: 완료")


def test_h7_exclaim():
    assert "H7" in codes("완료했다!")
    assert "H7" in codes("done!")
    assert "H7" not in codes("![alt](x.png)")  # 이미지 문법
    assert "H7" not in codes("조건 a != b 확인")  # != 는 제외


def test_h8_placeholder():
    assert "H8" in codes("담당자 홍길동")
    assert "H8" in codes("- TODO 나중에")
    assert "H8" not in codes("담당자 [확인 필요]")  # placeholder_marker
    assert "H8" not in codes("금액은 [금액 입력 필요]")


def test_h9_secret_all_text_files():
    assert "H9" in codes("token = sk-abcdefGHIJ0123456789klmno", "conf.py")
    assert "H9" in codes("key: glpat-abcdefGHIJ0123456789kl", "conf.yaml")
    assert "H9" not in codes("token = sk-xxxxxxxxxxxxxxxxxxxxxxxx", "conf.py")  # 자리표시자
    assert "H9" not in codes("key: your-token-here", "conf.yaml")


def test_h9_ignores_skips_and_offswitch():
    # H9 는 코드 펜스 안·doc_lint:off·정책 파일도 검사한다
    assert "H9" in codes("```\nAKIA0123456789ABCDEF\n```", "a.md")
    off = "---\ndoc_lint: off\n---\nsk-abcdefGHIJ0123456789klmno"
    assert codes(off, "a.md") == {"H9"}
    assert "H9" in codes("sk-abcdefGHIJ0123456789klmno", "STYLE.md")


def test_h9_secret_cannot_be_marker_disabled():
    txt = "<!-- doc-lint-allow secret: 예시라서 -->\nsk-abcdefGHIJ0123456789klmno"
    assert "H9" in codes(txt, "a.md")


def test_h10_office_binary(tmp_project):
    root = tmp_project
    for ext in ("docx", "pptx", "xlsx", "pdf"):
        r = d.run_pre({"tool_input": {"file_path": f"out.{ext}", "content": "x"}}, str(root))
        assert r and "block" in r and "H10" in r["block"]
    # 산문 파일은 H10 대상 아님
    r = d.run_pre({"tool_input": {"file_path": "out.md", "content": "정상"}}, str(root))
    assert r is None


# ─── 음성: frontmatter 안의 같은 문자열 ───────────────────────────────────────


def test_frontmatter_body_not_scanned():
    txt = "---\ntitle: 혁신적 제목 —\n---\n정상 본문"
    assert codes(txt, "a.md") == set()


# ─── 정책·마커 예외 ───────────────────────────────────────────────────────────


def test_policy_dash_allow():
    cfg = {"dash_policy": "allow"}
    assert "H1" not in codes("범위 1—2", cfg=cfg)


def test_policy_emoji_allow():
    cfg = {"emoji_policy": "allow"}
    assert "H6" not in codes("완료 \U0001f680", cfg=cfg)


def test_policy_exclaim_allow():
    cfg = {"exclaim_policy": "allow"}
    assert "H7" not in codes("완료!", cfg=cfg)


def test_policy_buzzword_warn_is_not_block():
    cfg = {"buzzword_policy": "warn"}
    fs = d.lint("혁신적 서비스", "a.md", cfg, soft=False)
    assert fs and all(f["severity"] == "warn" for f in fs if f["code"] == "H2")


def test_allow_terms_suppresses_buzzword():
    cfg = {"allow_terms": ["최적의 방안"]}
    assert "H2" not in codes("이것이 최적의 방안이다", cfg=cfg)
    assert "H2" in codes("이것이 최적의 솔루션이다", cfg=cfg)  # 다른 어구는 여전히 차단


def test_marker_disables_rule():
    txt = "<!-- doc-lint-allow dash: 인용문이라 -->\n범위 1—2"
    assert "H1" not in codes(txt)
    # 이유 없는 마커는 무효
    txt2 = "<!-- doc-lint-allow dash: -->\n범위 1—2"
    assert "H1" in codes(txt2)


def test_doc_lint_off_only_h9():
    txt = "---\ndoc_lint: off\n---\n혁신적 — 서비스!"
    assert codes(txt, "a.md") == set()


def test_policy_file_skips_prose_rules():
    txt = "혁신적 — 서비스!"
    assert codes(txt, "STYLE.md") == set()
    assert codes(txt, "docs/glossary.md") == set()
    assert codes(txt, "CLAUDE.md") == set()


def test_non_prose_text_only_h9():
    assert codes("혁신적 — 서비스!", "app.py") == set()
    assert codes("혁신적 — 서비스!", "conf.json") == set()


def test_skip_dirs():
    assert codes("혁신적 —!", "node_modules/x.md") == set()
    assert codes("sk-abcdefGHIJ0123456789klmno", ".venv/x.py") == set()


def test_windows_path_backslash():
    assert d.classify("docs\\arch\\x.md") == "prose"
    assert "H1" in codes("범위 1—2", "docs\\arch\\x.md")


# ─── 소프트 룰 S1~S18 (각 양성 2 · 음성 2 요지) ───────────────────────────────


def test_s1_rule_of_three():
    three = "- a\n- b\n- c\n\n텍스트\n\n- d\n- e\n- f\n\n텍스트\n\n- g\n- h\n- i\n"
    assert "S1" in codes(three)
    varied = "- a\n- b\n\n텍스트\n\n- d\n- e\n- f\n- g\n\n텍스트\n\n- h\n- i\n"
    assert "S1" not in codes(varied)


def test_s2_bold_label():
    txt = "\n".join(f"- **라벨{i}**: 설명" for i in range(4))
    assert "S2" in codes(txt)
    assert "S2" not in codes("- **라벨1**: 설명\n- **라벨2**: 설명")


def test_s3_closer():
    assert "S3" in codes("결론적으로 도입한다")
    assert "S3" not in codes("도입을 권고한다")


def test_s4_vague_adverb():
    assert "S4" in codes("다양한 것을 효과적으로 체계적으로 한다")
    assert "S4" not in codes("요약 API 두 개를 만든다")


def test_s5_can_stack():
    txt = "\n".join(f"작업 {i} 을 할 수 있습니다." for i in range(5))
    assert "S5" in codes(txt)
    assert "S5" not in codes("작업을 할 수 있습니다.")


def test_s6_same_starter():
    txt = "# 제목\n또한 A 한다. 또한 B 한다. 또한 C 한다."
    assert "S6" in codes(txt)
    assert "S6" not in codes("# 제목\n먼저 A 한다. 그다음 B 한다.")


def test_s7_colon_leadin():
    txt = "정리하면 다음과 같습니다:\n표는 다음과 같습니다:\n항목은 다음과 같습니다:"
    assert "S7" in codes(txt)
    assert "S7" not in codes("표는 아래와 같다")


def test_s8_generic_heading_en():
    assert "S8" in codes("# Introduction")
    assert "S8" in codes("## Conclusion")
    assert "S8" not in codes("# 개요")  # 한국어 관례 제목은 대상 아님
    assert "S8" not in codes("## 목적")


def test_s14_perfect_number():
    assert "S14" in codes("가동률 100% 달성")
    assert "S14" in codes("정확도 99.99%")
    assert "S14" not in codes("정확도 87%")


def test_s15_over_gloss():
    txt = " ".join(f"가나다(Term{i})" for i in range(10))
    assert "S15" in codes(txt)
    assert "S15" not in codes("게이트웨이(Gateway) 를 도입한다")


def test_s16_honorific_mix():
    txt = (
        "게이트웨이를 도입했습니다. 비용이 줄었습니다. 보안이 좋아졌습니다.\n"
        "설정은 간단하다. 폴백이 동작한다. 키가 분리된다."
    )
    assert "S16" in codes(txt)
    plain = "도입한다. 비용이 준다. 보안이 강화된다. 설정이 간단하다."
    assert "S16" not in codes(plain)


def test_s17_date_mix():
    assert "S17" in codes("작성 2026-09-04, 개정 2026. 9. 5.")
    assert "S17" not in codes("작성 2026-09-04, 개정 2026-09-05")


def test_s13_unsourced_number():
    src = "---\ndoc_type: 브리프\n---\n처리량이 40% 늘었다."
    assert "S13" in codes(src)
    ok = "---\ndoc_type: 브리프\n---\n처리량이 40% 늘었다(출처: 내부 측정)."
    assert "S13" not in codes(ok)
    # 설계서는 대상 아님
    other = "---\ndoc_type: 설계서\n---\n처리량이 40% 늘었다."
    assert "S13" not in codes(other)


def test_s18_glossary_term():
    cfg = {"_glossary_terms": ["쿠버네티스", "챗GPT"]}
    assert "S18" in codes("우리는 쿠버네티스로 배포한다", cfg=cfg)
    assert "S18" not in codes("우리는 Kubernetes 로 배포한다", cfg=cfg)


def test_soft_only_when_soft_true():
    assert "S3" not in codes("결론적으로 도입한다", soft=False)


# ─── 덱 룰 S9~S12 (.deck.md 만) ───────────────────────────────────────────────

DECK_HEAD = "---\ntitle: T\ntone_deck: 개조식\n---\n"


def test_s9_deck_long_bullet():
    long_ko = "가" * 45
    txt = DECK_HEAD + f"# 슬라이드\n## 헤드 메시지\n- {long_ko}"
    assert "S9" in codes(txt, "x.deck.md")
    assert "S9" not in codes(txt, "x.md")  # 문서에는 덱 룰 적용 안 함
    short = DECK_HEAD + "# 슬라이드\n## 헤드 메시지\n- 짧은 항목"
    assert "S9" not in codes(short, "x.deck.md")


def test_s10_deck_many_bullets():
    bullets = "\n".join(f"- 항목{i}" for i in range(7))
    txt = DECK_HEAD + "# 슬라이드\n## 헤드 메시지\n" + bullets
    assert "S10" in codes(txt, "x.deck.md")
    few = DECK_HEAD + "# 슬라이드\n## 헤드 메시지\n- a\n- b\n- c"
    assert "S10" not in codes(few, "x.deck.md")


def test_s11_deck_headline():
    no_head = DECK_HEAD + "# 슬라이드\n- 항목만 있다"
    assert "S11" in codes(no_head, "x.deck.md")
    long_head = DECK_HEAD + "# 슬라이드\n## " + ("가" * 61) + "\n- 항목"
    assert "S11" in codes(long_head, "x.deck.md")
    ok = DECK_HEAD + "# 슬라이드\n## 짧은 헤드 메시지\n- 항목"
    assert "S11" not in codes(ok, "x.deck.md")


def test_s12_deck_sentence_ending():
    txt = DECK_HEAD + "# 슬라이드\n## 헤드 메시지\n- 이것은 문장으로 끝납니다."
    assert "S12" in codes(txt, "x.deck.md")
    noun = DECK_HEAD + "# 슬라이드\n## 헤드 메시지\n- 파일럿 예산 확정 필요"
    assert "S12" not in codes(noun, "x.deck.md")


# ─── 안티 데드락 (7.5) ────────────────────────────────────────────────────────


def test_anti_deadlock(tmp_project, monkeypatch):
    root = str(tmp_project)
    # 상태 파일이 깨끗하도록 임시 디렉터리 격리
    import tempfile

    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_project / "_state"))
    (tmp_project / "_state").mkdir()
    inp = {"tool_input": {"file_path": "bad.md", "content": "범위 1—2"}}
    results = [d.run_pre(inp, root) for _ in range(4)]
    assert all("block" in (r or {}) for r in results[:3])
    assert "warn" in results[3]  # 4번째는 통과(경고)


# ─── CLI 3모드 subprocess ─────────────────────────────────────────────────────


def run_hook(args, stdin="", env=None, cwd=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(HOOK)] + args,
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=e,
        cwd=cwd,
    )


def test_cli_pre_blocks(tmp_project):
    env = {"CLAUDE_PROJECT_DIR": str(tmp_project)}
    payload = json.dumps({"tool_input": {"file_path": "x.md", "content": "범위 1—2"}})
    r = run_hook(["--pre"], stdin=payload, env=env)
    assert r.returncode == 2
    assert "H1" in r.stderr
    ok = json.dumps({"tool_input": {"file_path": "x.md", "content": "범위 1~2"}})
    r2 = run_hook(["--pre"], stdin=ok, env=env)
    assert r2.returncode == 0 and r2.stderr == ""


def test_cli_pre_noop_without_style(tmp_path):
    # STYLE.md 없으면 미설치 -> exit 0
    env = {"CLAUDE_PROJECT_DIR": str(tmp_path)}
    payload = json.dumps({"tool_input": {"file_path": "x.md", "content": "범위 1—2"}})
    r = run_hook(["--pre"], stdin=payload, env=env)
    assert r.returncode == 0


def test_cli_stop_blocks_once(tmp_git_project):
    root = tmp_git_project
    (root / "bad.md").write_text("결론적으로 도입한다\n범위 1—2", encoding="utf-8")
    env = {"CLAUDE_PROJECT_DIR": str(root)}
    r = run_hook(["--stop"], stdin="{}", env=env, cwd=str(root))
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["decision"] == "block"
    # stop_hook_active 면 통과
    r2 = run_hook(["--stop"], stdin=json.dumps({"stop_hook_active": True}), env=env, cwd=str(root))
    assert r2.returncode == 0 and r2.stdout == ""


def test_cli_all_exit_code(tmp_project):
    (tmp_project / "bad.md").write_text("범위 1—2", encoding="utf-8")
    (tmp_project / "good.md").write_text("범위 1~2", encoding="utf-8")
    env = {"CLAUDE_PROJECT_DIR": str(tmp_project)}
    r = run_hook(["--all", "."], env=env, cwd=str(tmp_project))
    assert r.returncode == 1
    assert "H1" in r.stdout
    # 깨끗한 디렉터리만
    (tmp_project / "bad.md").unlink()
    r2 = run_hook(["--all", "good.md"], env=env, cwd=str(tmp_project))
    assert r2.returncode == 0


def test_cli_version():
    r = run_hook(["--version"])
    assert r.returncode == 0 and r.stdout.strip() == d.VERSION


# ─── 픽스처 ───────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_project(tmp_path):
    (tmp_path / "STYLE.md").write_text("---\nai_work_skill: 0.1\n---\n# STYLE\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def tmp_git_project(tmp_project):
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_project))
    subprocess.run(["git", "add", "STYLE.md"], cwd=str(tmp_project))
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
        cwd=str(tmp_project),
    )
    return tmp_project
