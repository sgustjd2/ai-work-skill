"""litellm-ops MCP 서버(FastMCP, stdio). 툴은 core 를 얇게 감싼다.

읽기 툴은 그대로, 쓰기 툴(키 발급·차단, 팀 생성)은 LITELLM_OPS_ALLOW_WRITE=true 일 때만.
시크릿은 마스킹해 돌려준다. 오류는 ToolError 로 코드와 함께 낸다.
"""

from __future__ import annotations

import os

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from . import core, validate

mcp = FastMCP("litellm-ops")


def _ops() -> core.LiteLLMOps:
    return core.from_env()


def _guard(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except core.WriteDisabled as e:
        raise ToolError(f"WRITE_DISABLED: {e}") from e
    except core.OpsError as e:
        raise ToolError(f"GATEWAY_ERROR: {e}") from e


@mcp.tool
def gateway_health() -> dict:
    """게이트웨이 생존·준비·엔드포인트 상태. curl 없이 한 번에 본다."""
    return _guard(_ops().gateway_health)


@mcp.tool
def list_models(include_params: bool = False) -> dict:
    """등록된 모델 목록(제공자·api_base host·rpm/tpm)."""
    return _guard(_ops().list_models, include_params)


@mcp.tool
def test_completion(model: str, prompt: str = "ping", max_tokens: int = 16) -> dict:
    """모델 하나에 실제 completion 을 보내 지연·비용·샘플을 본다."""
    return _guard(_ops().test_completion, model, prompt, max_tokens)


@mcp.tool
def spend_summary(start_date: str, end_date: str, group_by: str = "api_key") -> dict:
    """기간 비용 요약. group_by: api_key|team|internal_user_id|customer."""
    return _guard(_ops().spend_summary, start_date, end_date, group_by)


@mcp.tool
def key_info(key: str) -> dict:
    """가상 키 정보(마스킹). 예산·사용량·모델·팀."""
    return _guard(_ops().key_info, key)


@mcp.tool
def team_info(team_id: str) -> dict:
    """팀 정보. 예산·사용량·모델·키 수."""
    return _guard(_ops().team_info, team_id)


@mcp.tool
def key_create(
    alias: str,
    models: list[str],
    max_budget: float,
    budget_duration: str = "1mo",
    team_id: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """가상 키 발급(쓰기). 전체 키는 응답에 한 번만 나온다."""
    return _guard(_ops().key_create, alias, models, max_budget, budget_duration, team_id, metadata)


@mcp.tool
def key_block(key: str) -> dict:
    """가상 키 차단(쓰기)."""
    return _guard(_ops().key_block, key)


@mcp.tool
def key_unblock(key: str) -> dict:
    """가상 키 차단 해제(쓰기)."""
    return _guard(_ops().key_unblock, key)


@mcp.tool
def team_create(
    alias: str, max_budget: float, budget_duration: str = "1mo", models: list[str] | None = None
) -> dict:
    """팀 생성·예산 설정(쓰기)."""
    return _guard(_ops().team_create, alias, max_budget, budget_duration, models)


@mcp.tool
def config_validate(path: str | None = None) -> dict:
    """config.yaml 을 검사한다(V1~V8). 네트워크 없음."""
    target = path or os.environ.get("LITELLM_CONFIG_PATH")
    if not target:
        raise ToolError("NO_CONFIG: path 또는 LITELLM_CONFIG_PATH 가 필요합니다.")
    return validate.config_validate(target)


@mcp.tool
def config_diff(path_a: str, path_b: str) -> dict:
    """두 config 의 model_list·fallbacks·settings 구조 차이."""
    return validate.config_diff(path_a, path_b)


def run():
    mcp.run()


if __name__ == "__main__":
    run()
