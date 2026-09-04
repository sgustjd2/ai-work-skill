---
doc_lint: off
---
# 골든 03 · 문서 요약 API 서비스 골격

설치된 프로젝트에서 아래를 그대로 붙여 넣고 결과를 `runs/<n>/` 에 저장한다.

---

문서 요약 API 서비스 골격 잡아줘. LiteLLM 게이트웨이 경유, 테스트·Docker·CI 포함.

---

**유도되는 슬롭**: 벤더 SDK 직접 호출, 설정 하드코딩, 테스트 없음

**기대**: scaffold 결과, pytest 통과, Dockerfile, .gitlab-ci.yml

**자동 검사(check_output.py 또는 수동)**: uv run pytest 0, docker build 0(도커 있을 때), ci_lint 통과, import_graph 위반 0
