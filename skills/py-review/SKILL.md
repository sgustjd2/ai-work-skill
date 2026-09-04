---
name: py-review
description: >
  Python·FastAPI·LLM 서비스 코드를 리뷰한다. "리뷰해줘", "MR 리뷰", "코드 봐줘", "PR 검토",
  "이 diff 문제 없나", "머지 전 확인", "보안 검토", "성능 검토" 요청에 반드시 쓴다. 로컬 diff 나
  GitLab MR(공식 MCP)을 읽고 심각도·파일:줄·수정안 형식으로 보고한다. 코멘트 게시는 사용자가 승인했을 때만 한다.
  리뷰 대상을 직접 고치지 않는다.
version: 0.1.0
user-invocable: true
argument-hint: "[MR 번호 | 브랜치 | 경로 | (없으면 작업 트리 diff)]"
allowed-tools:
  - Bash(git diff *)
  - Bash(git log *)
  - Bash(uv run pytest *)
  - Bash(uv run ruff *)
  - mcp__gitlab
---

# py-review

코드를 리뷰한다. 고치지 않는다. 체크리스트는 `references/checklist.md` 가 원본이다.

## 절차

1. 대상을 확보한다. 로컬은 `git diff`, GitLab MR 은 공식 MCP 의 `get_merge_request` 와 `get_merge_request_diffs`.

2. 변경 의도를 파악한다. MR 설명과 커밋 메시지를 읽는다.

3. `references/checklist.md` 를 읽고 검토한다. 변경한 함수의 호출자를 grep 으로 찾아 증상만 고친 수정인지 본다.

4. 테스트를 돌릴 수 있으면 돌린다(`uv run pytest`, `uv run ruff check`).

5. 형식을 고정해 보고한다.

```
## 리뷰: <대상>
판정: 승인 | 수정 후 승인 | 재작업
### 반드시 (block)
- [파일:줄] <문제> → <수정안> (근거: 체크리스트 ID)
### 권장 (should)
### 참고 (nit)
### 확인 질문 (작성자에게)
```

6. 게시는 사용자 승인 후 `save_merge_request_review` 또는 `save_note`(MCP)로 한다. 로컬 전용이면 보고만 하고 파일로 저장하지 않는다(요청 시만).

## 하지 않는 것

- 리뷰 대상을 직접 수정.
- 승인 없이 MR 에 코멘트 게시.
- 근거 없는 승인. 칭찬으로 시작하는 서론.
