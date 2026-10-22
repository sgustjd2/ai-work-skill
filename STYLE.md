---
ai_work_skill: 0.1
lang: ko
dash_policy: deny
emoji_policy: deny
exclaim_policy: deny
buzzword_policy: block
placeholder_marker: "[확인 필요]"
---

# 이 저장소의 doc_lint 설정

`.claude/settings.json` 의 훅(`templates/doc_lint.py`, `templates/py_format.py`)이 이 저장소의 편집에도 걸린다. `doc_lint` 는 루트에 `STYLE.md` 가 있어야 동작하므로(없으면 no-op) 이 파일이 그 설정이다. frontmatter 값은 `templates/doc_lint.py` 의 기본값과 같다.

문서·덱 산출물의 문서 계약(톤·번호·표기)은 이 파일이 아니라 `templates/STYLE.md` 와 `themes/*.json` 이다.
