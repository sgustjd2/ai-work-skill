"""LiteLLM 게이트웨이 운영 로직. httpx 로 admin API 를 부르고 시크릿을 마스킹한다.

쓰기(키 발급·차단, 팀 생성)는 allow_write 가 True 일 때만. 시크릿은 마스킹 외 어떤 형태로도
반환·로그하지 않는다(키 발급 응답의 1회성 전체 키 제외).
"""

from __future__ import annotations

import datetime as _dt
import os
from urllib.parse import urlparse

import httpx

KNOWN_PROVIDERS = (
    "azure/",
    "openai/",
    "anthropic/",
    "bedrock/",
    "vertex_ai/",
    "gemini/",
    "hosted_vllm/",
    "ollama/",
    "groq/",
    "mistral/",
    "cohere/",
    "together_ai/",
    "fireworks_ai/",
    "deepseek/",
    "xai/",
)
ROUTING_STRATEGIES = {
    "simple-shuffle",
    "latency-based-routing",
    "least-busy",
    "usage-based-routing",
    "cost-based-routing",
}


class WriteDisabled(Exception):
    """쓰기 게이트가 닫혀 있음."""


class OpsError(Exception):
    """게이트웨이 호출 실패."""


def mask_key(key: str | None) -> str:
    if not key:
        return ""
    s = str(key)
    return f"{s[:3]}…{s[-4:]}" if len(s) > 9 else "…"


def _host(url: str | None) -> str:
    if not url:
        return ""
    p = urlparse(url if "//" in str(url) else f"//{url}")
    return p.netloc or str(url)


def _now() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


class LiteLLMOps:
    def __init__(
        self,
        base_url: str,
        master_key: str = "",
        api_key: str | None = None,
        allow_write: bool = False,
        client: httpx.Client | None = None,
        config_path: str | None = None,
    ):
        self.base_url = str(base_url).rstrip("/")
        self.master_key = master_key
        self.api_key = api_key or master_key
        self.allow_write = allow_write
        self.config_path = config_path
        self._client = client or httpx.Client(
            base_url=self.base_url,
            timeout=10.0,
            headers={"Authorization": f"Bearer {master_key}"} if master_key else {},
        )

    # ── 읽기 ──
    def gateway_health(self) -> dict:
        out: dict = {
            "liveness": None,
            "readiness": None,
            "healthy": [],
            "unhealthy": [],
            "checked_at": _now(),
            "warnings": [],
        }
        try:
            r = self._client.get("/health/liveliness")
            out["liveness"] = "alive" if r.status_code == 200 else f"status {r.status_code}"
        except httpx.HTTPError as e:
            out["liveness"] = "unreachable"
            out["warnings"].append(f"liveliness: {e}")
        try:
            r = self._client.get("/health/readiness")
            out["readiness"] = (
                r.json()
                if r.headers.get("content-type", "").startswith("application/json")
                else r.text
            )
        except httpx.HTTPError as e:
            out["warnings"].append(f"readiness: {e}")
        try:
            r = self._client.get("/health")
            data = r.json()
            out["healthy"] = [
                {"model": m.get("model"), "api_base": _host(m.get("api_base"))}
                for m in data.get("healthy_endpoints", [])
            ]
            out["unhealthy"] = [
                {"model": m.get("model"), "api_base": _host(m.get("api_base"))}
                for m in data.get("unhealthy_endpoints", [])
            ]
        except httpx.HTTPError as e:
            out["warnings"].append(f"health: {e}")
        return out

    def list_models(self, include_params: bool = False) -> dict:
        data = self._json(self._client.get("/model/info"))
        rows = []
        for m in data.get("data", data if isinstance(data, list) else []):
            lp = m.get("litellm_params", {}) or {}
            model = lp.get("model", "")
            rows.append(
                {
                    "model_name": m.get("model_name"),
                    "provider": model.split("/", 1)[0] if "/" in model else "",
                    "model": model,
                    "api_base": _host(lp.get("api_base")),
                    "rpm": lp.get("rpm"),
                    "tpm": lp.get("tpm"),
                    "model_id": (m.get("model_info") or {}).get("id"),
                }
            )
        return {"models": rows, "count": len(rows), "warnings": []}

    def test_completion(self, model: str, prompt: str = "ping", max_tokens: int = 16) -> dict:
        import time as _time

        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        t0 = _time.perf_counter()
        r = self._client.post(
            "/v1/chat/completions",
            timeout=60.0,
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            },
        )
        latency = (_time.perf_counter() - t0) * 1000
        data = self._json(r)
        sample = ""
        try:
            sample = data["choices"][0]["message"]["content"][:60]
        except (KeyError, IndexError, TypeError):
            pass
        cost = r.headers.get("x-litellm-response-cost")
        return {
            "model": data.get("model", model),
            "latency_ms": round(latency, 1) if latency else None,
            "cost_usd": float(cost) if cost else None,
            "usage": data.get("usage", {}),
            "sample": sample,
            "warnings": [],
        }

    def spend_summary(self, start_date: str, end_date: str, group_by: str = "api_key") -> dict:
        try:
            data = self._json(
                self._client.get(
                    "/global/spend/report",
                    params={"start_date": start_date, "end_date": end_date, "group_by": group_by},
                )
            )
            rows = self._spend_rows(data, group_by)
            return {
                "rows": rows,
                "total_usd": round(sum(r["spend_usd"] for r in rows), 6),
                "group_by": group_by,
                "warnings": [],
            }
        except (OpsError, httpx.HTTPError):
            data = self._json(self._client.get("/spend/logs", params={"summarize": "true"}))
            rows = self._spend_rows(data, group_by)
            return {
                "rows": rows,
                "total_usd": round(sum(r["spend_usd"] for r in rows), 6),
                "group_by": group_by,
                "warnings": ["global/spend/report 실패, spend/logs 로 폴백"],
            }

    @staticmethod
    def _spend_rows(data, group_by) -> list[dict]:
        rows = []
        items = data if isinstance(data, list) else data.get("rows", data.get("data", []))
        for it in items or []:
            if not isinstance(it, dict):
                continue
            rows.append(
                {
                    "group": it.get(group_by)
                    or it.get("group")
                    or it.get("api_key")
                    or it.get("team_id")
                    or "?",
                    "spend_usd": float(it.get("spend", it.get("total_spend", 0)) or 0),
                    "tokens": int(it.get("total_tokens", it.get("tokens", 0)) or 0),
                }
            )
        return rows

    def key_info(self, key: str) -> dict:
        data = self._json(self._client.get("/key/info", params={"key": key}))
        info = data.get("info", data)
        return {
            "key_masked": mask_key(key),
            "alias": info.get("key_alias"),
            "models": info.get("models", []),
            "spend": info.get("spend"),
            "max_budget": info.get("max_budget"),
            "budget_duration": info.get("budget_duration"),
            "expires": info.get("expires"),
            "team_id": info.get("team_id"),
            "blocked": info.get("blocked"),
            "warnings": [],
        }

    def team_info(self, team_id: str) -> dict:
        data = self._json(self._client.get("/team/info", params={"team_id": team_id}))
        info = data.get("team_info", data)
        return {
            "team_id": team_id,
            "alias": info.get("team_alias"),
            "spend": info.get("spend"),
            "max_budget": info.get("max_budget"),
            "budget_duration": info.get("budget_duration"),
            "models": info.get("models", []),
            "keys_count": len(info.get("keys", []) or []),
            "warnings": [],
        }

    # ── 쓰기(게이트) ──
    def _require_write(self):
        if not self.allow_write:
            raise WriteDisabled(
                "읽기 전용 모드입니다. .mcp.json env 에 LITELLM_OPS_ALLOW_WRITE=true 를 설정하세요."
            )

    def key_create(
        self,
        alias: str,
        models: list[str],
        max_budget: float,
        budget_duration: str = "1mo",
        team_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        self._require_write()
        payload = {
            "key_alias": alias,
            "models": models,
            "max_budget": max_budget,
            "budget_duration": budget_duration,
        }
        if team_id:
            payload["team_id"] = team_id
        if metadata:
            payload["metadata"] = metadata
        data = self._json(self._client.post("/key/generate", json=payload))
        full = data.get("key", "")
        return {
            "key_masked": mask_key(full),
            "key_full_once": full,
            "alias": alias,
            "max_budget": max_budget,
            "note": "전체 키는 이 응답에 한 번만 나옵니다. 지금 비밀 저장소에 넣으세요.",
            "warnings": [],
        }

    def key_block(self, key: str) -> dict:
        self._require_write()
        self._json(self._client.post("/key/block", json={"key": key}))
        return {"key_masked": mask_key(key), "blocked": True, "warnings": []}

    def key_unblock(self, key: str) -> dict:
        self._require_write()
        self._json(self._client.post("/key/unblock", json={"key": key}))
        return {"key_masked": mask_key(key), "blocked": False, "warnings": []}

    def team_create(
        self,
        alias: str,
        max_budget: float,
        budget_duration: str = "1mo",
        models: list[str] | None = None,
    ) -> dict:
        self._require_write()
        payload = {
            "team_alias": alias,
            "max_budget": max_budget,
            "budget_duration": budget_duration,
        }
        if models:
            payload["models"] = models
        data = self._json(self._client.post("/team/new", json=payload))
        return {
            "team_id": data.get("team_id"),
            "alias": alias,
            "max_budget": max_budget,
            "warnings": [],
        }

    # ── 공통 ──
    @staticmethod
    def _json(resp: httpx.Response) -> dict:
        if resp.status_code >= 400:
            req = resp.request
            raise OpsError(f"{req.method} {req.url.path} → {resp.status_code}: {resp.text[:150]}")
        try:
            return resp.json()
        except ValueError as e:
            raise OpsError(f"JSON 파싱 실패: {e}") from e

    def close(self):
        self._client.close()


def from_env(client: httpx.Client | None = None) -> LiteLLMOps:
    return LiteLLMOps(
        base_url=os.environ.get("LITELLM_BASE_URL", "http://localhost:4000"),
        master_key=os.environ.get("LITELLM_MASTER_KEY", ""),
        api_key=os.environ.get("LITELLM_API_KEY") or None,
        allow_write=os.environ.get("LITELLM_OPS_ALLOW_WRITE", "false").lower() == "true",
        config_path=os.environ.get("LITELLM_CONFIG_PATH"),
        client=client,
    )
