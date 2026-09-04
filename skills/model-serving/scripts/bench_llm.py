#!/usr/bin/env python3
"""bench_llm.py — OpenAI 호환 엔드포인트(게이트웨이·vLLM) 처리량·지연 벤치 (FR-29).

동시성별로 TTFT(첫 토큰까지) p50/p95, tokens/s, 실패율을 잰다. 표준 라이브러리만 쓴다.
실제 엔드포인트가 필요하므로 기본 스위트에서는 순수 통계 함수만 테스트하고, 실행은 수동으로 한다.

  python bench_llm.py --base-url http://localhost:4000 --model gpt-4o \
      --concurrency 1,4,16 --prompt-tokens 512 --max-tokens 256 [--api-key sk-..] [--requests 8]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
import time
import urllib.request


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (p / 100)
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def summarize(results: list[dict]) -> dict:
    ok = [r for r in results if r["ok"]]
    ttfts = [r["ttft_ms"] for r in ok if r["ttft_ms"] is not None]
    tps = [r["tokens_per_s"] for r in ok if r["tokens_per_s"]]
    return {
        "requests": len(results),
        "failures": len(results) - len(ok),
        "failure_rate": round((len(results) - len(ok)) / len(results), 3) if results else 0,
        "ttft_p50_ms": round(percentile(ttfts, 50), 1),
        "ttft_p95_ms": round(percentile(ttfts, 95), 1),
        "tokens_per_s_mean": round(sum(tps) / len(tps), 1) if tps else 0,
    }


def _one_request(base_url: str, api_key: str, model: str, prompt: str, max_tokens: int) -> dict:
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "stream": True,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    t0 = time.perf_counter()
    ttft = None
    tokens = 0
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw in resp:
                line = raw.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                chunk = line[len("data:") :].strip()
                if chunk == "[DONE]":
                    break
                if ttft is None:
                    ttft = (time.perf_counter() - t0) * 1000
                tokens += 1
        total = time.perf_counter() - t0
        return {
            "ok": True,
            "ttft_ms": ttft,
            "total_ms": total * 1000,
            "tokens_per_s": tokens / total if total else 0,
        }
    except Exception as e:  # noqa: BLE001 - 벤치는 실패를 결과로 기록한다
        return {"ok": False, "ttft_ms": None, "total_ms": None, "tokens_per_s": 0, "error": str(e)}


def run(base_url, api_key, model, concurrencies, prompt_tokens, max_tokens, requests) -> dict:
    prompt = "테스트 " * max(1, prompt_tokens // 2)
    out = {}
    for c in concurrencies:
        with concurrent.futures.ThreadPoolExecutor(max_workers=c) as ex:
            futs = [
                ex.submit(_one_request, base_url, api_key, model, prompt, max_tokens)
                for _ in range(max(requests, c))
            ]
            results = [f.result() for f in futs]
        out[str(c)] = summarize(results)
    return {"model": model, "base_url": base_url, "by_concurrency": out}


def main(argv=None):
    ap = argparse.ArgumentParser(description="LLM 엔드포인트 벤치마크")
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--concurrency", default="1,4,16")
    ap.add_argument("--prompt-tokens", type=int, default=512)
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--api-key", default="sk-bench")
    ap.add_argument("--requests", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    conc = [int(x) for x in a.concurrency.split(",")]
    r = run(a.base_url, a.api_key, a.model, conc, a.prompt_tokens, a.max_tokens, a.requests)
    if a.json:
        sys.stdout.write(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    else:
        for c, s in r["by_concurrency"].items():
            sys.stdout.write(
                f"동시성 {c}: TTFT p50 {s['ttft_p50_ms']}ms · p95 {s['ttft_p95_ms']}ms · "
                f"{s['tokens_per_s_mean']} tok/s · 실패율 {s['failure_rate']}\n"
            )
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
