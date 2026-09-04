---
doc_lint: off
---
# 골든 05 · Azure 2리전 + Bedrock 폴백 + 팀별 예산 config

설치된 프로젝트에서 아래를 그대로 붙여 넣고 결과를 `runs/<n>/` 에 저장한다.

---

Azure gpt-4o 두 리전에 Bedrock Claude 폴백, 팀별 예산으로 LiteLLM config.yaml 만들어줘.

---

**유도되는 슬롭**: 키 인라인, 폴백 오타, 헬스체크 누락

**기대**: config_validate 통과, .env.example 동기

**자동 검사(check_output.py 또는 수동)**: config-validate error 0(V1~V8)
