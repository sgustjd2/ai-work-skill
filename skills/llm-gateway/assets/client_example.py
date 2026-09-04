"""게이트웨이 연결 예시. 앱은 벤더 SDK 대신 OpenAI 호환 엔드포인트(게이트웨이)만 부른다.

- base_url 은 게이트웨이, api_key 는 팀 가상 키.
- user·metadata.tags 로 비용 귀속·추적을 남긴다.
- 스트리밍과 구조화 출력, 재시도 예시를 함께 담았다.
"""

from __future__ import annotations

import os

from openai import OpenAI

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "http://localhost:4000"),
    api_key=os.environ.get("LLM_API_KEY", "sk-team-key"),
    max_retries=2,
)

COMMON = {"user": "summary-service", "extra_body": {"metadata": {"tags": ["summary", "prod"]}}}


def chat(message: str, model: str = "gpt-4o") -> str:
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": message}], timeout=30, **COMMON
    )
    return resp.choices[0].message.content


def stream(message: str, model: str = "gpt-4o"):
    with client.chat.completions.stream(
        model=model, messages=[{"role": "user", "content": message}], **COMMON
    ) as s:
        for event in s:
            if event.type == "content.delta":
                yield event.delta


def structured(message: str, schema: dict, model: str = "gpt-4o") -> dict:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}],
        response_format={"type": "json_schema", "json_schema": {"name": "out", "schema": schema}},
        **COMMON,
    )
    import json

    return json.loads(resp.choices[0].message.content)


if __name__ == "__main__":
    print(chat("한 줄로 인사해줘"))
