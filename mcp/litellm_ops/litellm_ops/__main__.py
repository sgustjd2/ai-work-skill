"""litellm-ops CLI. MCP 서버와 같은 core 를 부른다.

  python -m litellm_ops health
  python -m litellm_ops models
  python -m litellm_ops test-completion <model> [--prompt ..] [--max-tokens 16]
  python -m litellm_ops spend <start> <end> [--group-by api_key]
  python -m litellm_ops key-info <key>
  python -m litellm_ops team-info <team_id>
  python -m litellm_ops config-validate <config.yaml>
  python -m litellm_ops config-diff <a.yaml> <b.yaml>
쓰기(key-create/block/unblock, team-create)는 LITELLM_OPS_ALLOW_WRITE=true 일 때만.
종료코드: 0 성공 · 1 게이트웨이·검증 오류 · 2 쓰기 잠김
"""

from __future__ import annotations

import argparse
import json
import sys

from . import core, validate


def _print(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="litellm-ops")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("health")
    sub.add_parser("models")
    p = sub.add_parser("test-completion")
    p.add_argument("model")
    p.add_argument("--prompt", default="ping")
    p.add_argument("--max-tokens", type=int, default=16)
    p = sub.add_parser("spend")
    p.add_argument("start")
    p.add_argument("end")
    p.add_argument("--group-by", default="api_key")
    p = sub.add_parser("key-info")
    p.add_argument("key")
    p = sub.add_parser("team-info")
    p.add_argument("team_id")
    p = sub.add_parser("config-validate")
    p.add_argument("path")
    p = sub.add_parser("config-diff")
    p.add_argument("path_a")
    p.add_argument("path_b")

    a = ap.parse_args(argv)
    if a.cmd == "config-validate":
        r = validate.config_validate(a.path)
        _print(r)
        return 0 if r["ok"] else 1
    if a.cmd == "config-diff":
        _print(validate.config_diff(a.path_a, a.path_b))
        return 0

    ops = core.from_env()
    try:
        if a.cmd == "health":
            _print(ops.gateway_health())
        elif a.cmd == "models":
            _print(ops.list_models())
        elif a.cmd == "test-completion":
            _print(ops.test_completion(a.model, a.prompt, a.max_tokens))
        elif a.cmd == "spend":
            _print(ops.spend_summary(a.start, a.end, a.group_by))
        elif a.cmd == "key-info":
            _print(ops.key_info(a.key))
        elif a.cmd == "team-info":
            _print(ops.team_info(a.team_id))
    except core.WriteDisabled as e:
        sys.stderr.write(f"[litellm-ops] {e}\n")
        return 2
    except core.OpsError as e:
        sys.stderr.write(f"[litellm-ops] 게이트웨이 오류: {e}\n")
        return 1
    finally:
        ops.close()
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
