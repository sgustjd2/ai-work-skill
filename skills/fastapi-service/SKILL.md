---
name: fastapi-service
description: >
  FastAPI 기반 생성형 AI 서비스의 프로젝트 골격을 만들거나 기존 서비스를 표준 구조로 맞춘다. "서비스 골격",
  "FastAPI 프로젝트 생성", "API 서버 만들어줘", "요약/챗/RAG API", "LLM 호출 서비스", "개발 환경 구축",
  "Dockerfile·compose", "설정·로깅 표준", "SSE 스트리밍 엔드포인트", "헬스체크" 요청에 반드시 쓴다.
  LLM 호출은 LiteLLM 게이트웨이 경유만 허용하고, 설정은 환경변수, 테스트·Docker·CI 를 함께 만든다.
  프론트엔드·데이터 파이프라인·모델 학습 코드는 대상이 아니다.
version: 0.1.0
user-invocable: true
argument-hint: "[서비스 이름과 기능 한 줄]"
allowed-tools:
  - Bash(python */skills/fastapi-service/scripts/*.py *)
  - Bash(uv *)
  - Bash(docker build *)
---

# fastapi-service

FastAPI 서비스 골격을 만든다. LLM 호출은 게이트웨이만 거친다. 규약은 `../../references/python-conventions.md` 가 원본이다. 여기에 복사하지 않는다.

## 절차

1. 기존 프로젝트면 먼저 구조를 진단한다. `scripts/route_table.py --app <pkg>.main:create_app` 로 라우트를 덤프하고 바꿀 것을 표로 제안한다. 곧바로 고치지 않는다.

2. 신규면 서비스 리드를 한 줄로 선언한다.
   `서비스: <이름> · 기능 <한 줄> · 패턴 <채팅|요약|RAG|에이전트|배치> · 외부 의존 <게이트웨이|DB|Redis|없음> · 배포 <컨테이너> · 인증 <없음|API 키|SSO>`

3. 골격을 만든다.
   ```
   python skills/fastapi-service/scripts/scaffold.py --name <pkg> --target <dir> [--with-db] [--with-redis] [--with-sse] [--with-auth] [--with-rag] [--with-jobs] [--with-otel]
   ```
   `--with-rag` 는 `--with-db` 를 함의한다. 생성 트리를 사용자에게 보인다.

4. 기능 코드를 채운다. `../../references/python-conventions.md` 를 읽는다. 패턴이 RAG·에이전트·비동기면 `../../references/genai-patterns.md` 도 읽는다. 프롬프트는 코드에 인라인하지 않고 `<pkg>/prompts/*.md` 에 둔다.

5. 검증한다. `uv sync && uv run pytest` 통과, `docker build` 성공을 확인한다. CI 는 `gitlab-ci` 스킬로 추가한다(원치 않으면 생략).

6. 인터페이스 표가 필요하면 `route_table.py --md` 의 출력을 설계서에 그대로 붙인다. 손으로 옮겨 쓰지 않는다.

## 규칙 요약

핸들러에서 블로킹 I/O 금지. 모든 외부 호출에 타임아웃·재시도. 벤더 SDK 키를 앱에 두지 않는다(게이트웨이만). 로그에 프롬프트·개인정보 기본 미기록. 설정은 환경변수만. 레이어 방향 api → services → infra. 상태 저장은 infra 만. LLM 출력은 스키마로 검증하고 실패 시 한 번 재요청. 사용자 입력은 프롬프트의 데이터 자리에만.

## 하지 않는 것

- 벤더 SDK 를 앱에서 직접 호출(게이트웨이만).
- 설정·시크릿을 코드에 인라인.
- 테스트·Dockerfile 없이 골격만 넘기기.
- 프론트엔드·데이터 파이프라인·모델 학습 코드.
