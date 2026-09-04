---
doc_lint: off
---
# 골든 08 · services 순환 import 정리 계획

설치된 프로젝트에서 아래를 그대로 붙여 넣고 결과를 `runs/<n>/` 에 저장한다.

---

services 패키지의 순환 import 를 정리하는 계획을 세워줘.

---

**유도되는 슬롭**: 한 번에 다 옮기기, 동작 변경 섞기

**기대**: import_graph 전후, ADR, 단계별 검증

**자동 검사(check_output.py 또는 수동)**: ADR 파일 존재, 순환 0
