"""M3 스크립트 단위 테스트: vram_estimate, bench_llm 순수 통계."""

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.deterministic
ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str):
    p = ROOT / rel
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_vram_weights_exact():
    ve = _load("skills/model-serving/scripts/vram_estimate.py")
    r = ve.estimate(32, "fp16", ctx=8192, batch=1)
    assert r["weights_gb"] == 64.0  # 32B * 2 bytes
    r4 = ve.estimate(32, "int4", ctx=8192, batch=1)
    assert r4["weights_gb"] == 16.0  # 32B * 0.5
    assert r["total_gb"] > r["weights_gb"]  # KV + 여유 포함


def test_vram_gpu_count():
    ve = _load("skills/model-serving/scripts/vram_estimate.py")
    r = ve.estimate(70, "fp16", ctx=4096, batch=1)
    # 70B fp16 = 140GB 가중치, 80GB GPU 로 2장 이상
    assert r["gpus_needed"]["80GB"] >= 2


def test_vram_bad_dtype():
    ve = _load("skills/model-serving/scripts/vram_estimate.py")
    with pytest.raises(ValueError):
        ve.estimate(7, "float9")


def test_bench_percentile():
    b = _load("skills/model-serving/scripts/bench_llm.py")
    assert b.percentile([10, 20, 30, 40], 50) == 25.0
    assert b.percentile([5], 95) == 5
    assert b.percentile([], 50) == 0.0


def test_bench_summarize():
    b = _load("skills/model-serving/scripts/bench_llm.py")
    results = [
        {"ok": True, "ttft_ms": 100, "tokens_per_s": 50},
        {"ok": True, "ttft_ms": 200, "tokens_per_s": 40},
        {"ok": False, "ttft_ms": None, "tokens_per_s": 0},
    ]
    s = b.summarize(results)
    assert s["failures"] == 1
    assert s["failure_rate"] == round(1 / 3, 3)
    assert s["ttft_p50_ms"] == 150.0
