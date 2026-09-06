"""humanize_scan: 확인 후보·평균값 신호·재료 밀도 (FR-39). PRD 8.14."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.deterministic
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "humanize" / "scripts" / "humanize_scan.py"


def _load():
    spec = importlib.util.spec_from_file_location("humanize_scan", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


AVERAGE = """# 도입 검토

신규 서버 도입은 업무에 큰 도움이 됩니다. 누구나 동의하는 방향입니다.

최근 조사에 따르면 도입 기업의 70%가 검증 기간을 절반으로 줄였습니다. 이는 의미 있는 수치입니다.

체계적인 관리가 필요합니다. 관리가 있어야 안정적입니다.

전문가들은 단계적 도입을 권합니다. 단계가 있어야 위험이 줄어듭니다.

작은 것부터 꾸준히 실천해 보세요. 그러면 결과가 따라옵니다.
"""

CONCRETE = """# 도입 검토

RTX 5090 32GB 서버 2대 도입을 권고한다.

현재 검증 환경은 8~9B급 모델까지만 돌아간다.
파일럿에서 폴백 응답 형식 오류가 2건 났다(출처: 파일럿 회고 메모 2026-08-20).
클라우드 GPU 는 전시 현장 시연에 쓸 수 없어 제외했다.

남은 위험은 부품 수급에 따른 견적 변동이다.

발주 직전 견적을 재확인한다. 담당은 개발연구본부, 기한은 10월 15일이다.
"""


def test_verify_unsourced():
    r = _load().scan(AVERAGE)
    hit = [v for v in r["verify"] if "70%" in v["sentence"]]
    assert hit and hit[0]["unsourced"]
    assert {"수치", "출처"} <= set(hit[0]["kinds"])
    assert hit[0]["line"] == 5


def test_verify_sourced_paragraph():
    r = _load().scan(CONCRETE)
    hit = [v for v in r["verify"] if "2건" in v["sentence"]]
    assert hit and not hit[0]["unsourced"]


def test_average_signals():
    r = _load().scan(AVERAGE)
    names = {s["name"] for s in r["signals"]}
    assert {"generalization", "moral-closer", "uniform-paragraphs"} <= names
    assert r["material_suspect"]


def test_concrete_text_is_clean():
    r = _load().scan(CONCRETE)
    names = {s["name"] for s in r["signals"]}
    assert not names & {"generalization", "moral-closer", "uniform-paragraphs", "bullet-heavy"}
    assert r["material_density"] >= 0.5 and not r["material_suspect"]


def test_bullet_heavy_and_stock_ending():
    text = (
        "# 목록\n\n"
        + "\n".join(f"- 항목 {i} 는 도움이 됩니다." for i in range(10))
        + "\n\n한 문단.\n"
    )
    r = _load().scan(text)
    names = {s["name"] for s in r["signals"]}
    assert {"bullet-heavy", "stock-ending"} <= names


def test_skips_fence_frontmatter_comment():
    text = (
        "---\ntitle: 연구에 따르면 99%\n---\n\n<!-- humanize: 주장 연구 70% -->\n\n"
        "```\n최근 조사에 따르면 70%\n```\n\n평범한 설명 문장이다.\n"
    )
    r = _load().scan(text)
    assert r["verify"] == []


def test_cli_json(tmp_path):
    f = tmp_path / "a.md"
    f.write_text(AVERAGE, encoding="utf-8")
    p = subprocess.run(
        [sys.executable, "-X", "utf8", str(SCRIPT), str(f), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert p.returncode == 0
    out = json.loads(p.stdout)
    assert out["verify"] and out["file"].endswith("a.md")
