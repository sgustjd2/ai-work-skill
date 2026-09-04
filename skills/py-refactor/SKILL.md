---
name: py-refactor
description: >
  Python 코드의 모듈화·구조 개선·리팩토링을 계획하고 안전하게 수행한다. "리팩토링", "구조 개선", "모듈 분리",
  "순환 import", "god 파일 쪼개기", "레이어 정리", "중복 제거", "기술 부채 정리", "패키지 재구성" 요청에 반드시 쓴다.
  동작 변화 없이 작은 단위로 옮기고, 이동 전 특성화 테스트를 만들며, 계획을 ADR 로 남긴다. 기능 추가는 하지 않는다.
version: 0.1.0
user-invocable: true
argument-hint: "[대상 패키지·모듈]"
allowed-tools:
  - Bash(python */skills/py-refactor/scripts/import_graph.py *)
  - Bash(uv run pytest *)
  - Bash(git *)
---

# py-refactor

구조를 개선한다. 동작은 바꾸지 않는다. 규약은 `../../references/python-conventions.md` 가 원본이다.

## 절차

1. `scripts/import_graph.py <pkg>` 로 순환·레이어 위반·팬인/팬아웃 상위·긴 파일을 본다.

2. 리팩토링 리드를 한 줄로 선언한다.
   `리팩토링: <대상> · 목표 <순환 제거|레이어 분리|파일 분할|중복 제거> · 범위 <파일 n개> · 동작 변화 없음`

3. 특성화 테스트를 먼저 만든다. 현재 동작을 고정한다. 없으면 `py-test` 로 만든다.

4. 이동 계획을 표로 만든다. 무엇을 어디로, 순서, 각 단계 뒤 실행할 검증. `docs/adr/NNNN-<제목>.md` 로 남긴다(doc-write ADR 골격).

5. 단계마다 `uv run pytest` 와 `import_graph.py` 를 다시 돌린다. 사용자가 커밋을 원하면 단계당 커밋 하나.

6. 완료 보고에 전후 지표(순환 수, 위반 수, 최대 파일 길이)를 넣는다.

## 규칙

- 리팩토링 MR 에 동작 변경을 섞지 않는다.
- 공개 함수 시그니처를 유지한다. 어댑터로 감싸고 나중에 제거한다.
- `__init__.py` 재수출로 호환을 유지한 뒤 호출자를 옮긴다.
- 한 MR 은 한 이동. import 는 api → services → infra 방향.

## 하지 않는 것

- 동작을 바꾸기(리팩토링과 기능 변경 분리).
- 특성화 테스트 없이 옮기기.
- 한 번에 다 옮기기.
