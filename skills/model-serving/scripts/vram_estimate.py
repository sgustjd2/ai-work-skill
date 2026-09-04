#!/usr/bin/env python3
"""vram_estimate.py — LLM 서빙 VRAM 추정 (FR-29). 표준 라이브러리만.

가중치 + KV 캐시 + 여유(20%)를 더해 필요한 VRAM 과 GPU 수를 낸다.

  python vram_estimate.py --params 32 --dtype fp16 --ctx 32768 --batch 8 [--layers L --hidden H]

추정치다. 실제 사용량은 커널·프레임워크·단편화로 달라진다.
"""

from __future__ import annotations

import argparse
import json
import sys

DTYPE_BYTES = {
    "fp32": 4,
    "fp16": 2,
    "bf16": 2,
    "fp8": 1,
    "int8": 1,
    "int4": 0.5,
    "awq": 0.5,
    "gptq": 0.5,
}
# 파라미터 규모별 기본 아키텍처(레이어 수, hidden). 값을 주면 그것을 쓴다.
PRESETS = [
    (8, 32, 4096),
    (14, 48, 5120),
    (32, 64, 5120),
    (70, 80, 8192),
    (1e9, 96, 12288),
]
GPU_CARDS = [("24GB", 24), ("48GB", 48), ("80GB", 80)]


def _preset(params_b: float) -> tuple[int, int]:
    for cap, layers, hidden in PRESETS:
        if params_b <= cap:
            return layers, hidden
    return 96, 12288


def estimate(
    params_b: float,
    dtype: str = "fp16",
    ctx: int = 8192,
    batch: int = 1,
    layers: int | None = None,
    hidden: int | None = None,
    kv_dtype: str = "fp16",
) -> dict:
    wbytes = DTYPE_BYTES.get(dtype.lower())
    if wbytes is None:
        raise ValueError(f"알 수 없는 dtype: {dtype} (지원: {', '.join(DTYPE_BYTES)})")
    pl, ph = _preset(params_b)
    layers = layers or pl
    hidden = hidden or ph

    weights_gb = params_b * wbytes  # 10억 파라미터 * bytes = GB
    kv_bytes = DTYPE_BYTES.get(kv_dtype.lower(), 2)
    # KV 캐시: 2(K,V) * layers * ctx * batch * hidden * kv_bytes
    kv_gb = 2 * layers * ctx * batch * hidden * kv_bytes / 1e9
    subtotal = weights_gb + kv_gb
    overhead_gb = subtotal * 0.20
    total_gb = subtotal + overhead_gb

    gpus = {}
    for name, cap in GPU_CARDS:
        gpus[name] = -(-total_gb // cap)  # ceil
    return {
        "params_b": params_b,
        "dtype": dtype,
        "ctx": ctx,
        "batch": batch,
        "layers": layers,
        "hidden": hidden,
        "weights_gb": round(weights_gb, 2),
        "kv_cache_gb": round(kv_gb, 2),
        "overhead_gb": round(overhead_gb, 2),
        "total_gb": round(total_gb, 2),
        "gpus_needed": {k: int(v) for k, v in gpus.items()},
        "note": "추정치. 실제는 프레임워크·단편화로 다를 수 있다.",
    }


def _report(r: dict) -> str:
    lines = [
        f"[vram] {r['params_b']}B · {r['dtype']} · ctx {r['ctx']} · batch {r['batch']} "
        f"(layers {r['layers']}, hidden {r['hidden']})",
        f"  가중치 {r['weights_gb']} GB + KV {r['kv_cache_gb']} GB + 여유 {r['overhead_gb']} GB "
        f"= {r['total_gb']} GB",
        "  GPU 수: " + ", ".join(f"{k} {v}장" for k, v in r["gpus_needed"].items()),
        "  " + r["note"],
    ]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="LLM 서빙 VRAM 추정")
    ap.add_argument("--params", type=float, required=True, help="파라미터(10억 단위, 예: 32)")
    ap.add_argument("--dtype", default="fp16")
    ap.add_argument("--ctx", type=int, default=8192)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--layers", type=int, default=None)
    ap.add_argument("--hidden", type=int, default=None)
    ap.add_argument("--kv-dtype", default="fp16")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        r = estimate(a.params, a.dtype, a.ctx, a.batch, a.layers, a.hidden, a.kv_dtype)
    except ValueError as e:
        sys.stderr.write(f"[vram] {e}\n")
        return 2
    sys.stdout.write((json.dumps(r, ensure_ascii=False, indent=2) if a.json else _report(r)) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
