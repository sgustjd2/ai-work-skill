---
name: doc-write
description: >
  기업·연구개발 조직의 문서를 한국 기업 문서체로 쓴다. 아키텍처 설계서, 기술 검토서, 검토보고서, 개발 가이드,
  온보딩 가이드, 운영 런북, ADR(설계 결정 기록), 인터페이스 정의서, 회의록, 기술 브리프, README, 교육 자료.
  "설계서 써줘", "문서 만들어줘", "가이드 작성", "런북", "ADR", "검토보고서", "docx로", "워드로", "보고서 초안",
  "AS-IS/TO-BE", "구성도 포함 문서" 요청에 반드시 쓴다. STYLE.md 와 테마만 따르고 AI 문체(상투어·em-dash·이모지·
  굵은 라벨 목록)를 피한다. 결과는 Markdown(.doc.md)이며 docx 가 필요하면 docgen 으로 렌더링한다.
  기존 문서의 수정, 동료 문서에 대한 리뷰 의견, 경영진용 1쪽 요약, 검토 의견에 대한 답변도 이 스킬이 한다.
  슬라이드·덱은 deck-write, 주간보고 xlsx 는 대상이 아니다.
version: 0.1.0
user-invocable: true
argument-hint: "[문서 유형과 주제 | 수정할 파일 | 리뷰할 파일]"
allowed-tools:
  - Bash(python .claude/hooks/doc_lint.py *)
  - Bash(uv run --project * python -m docgen *)
  - Bash(python -m docgen *)
  - mcp__docgen
---

# doc-write

한국 기업 문서체로 문서를 쓴다. 색·폰트·회사 사실은 `STYLE.md` 와 테마가 원본이다. 여기에 복사하지 않는다. 문서는 Edit/Write 도구로 쓴다. Bash 리다이렉트로 쓰면 훅을 우회하므로 하지 않는다.

## 절차

0. 모드를 한 줄로 정한다.
   - `신규`: 새 문서.
   - `수정`: 기존 `.doc.md` 또는 docx 를 `docx_to_md` 로 읽고, 바뀐 부분만 다시 쓴다. 원본 구조를 유지한다.
   - `리뷰 의견`: 동료 문서를 `references/preflight-doc.md` 와 `references/writing-rules-ko.md` 로 읽고 `수정 필요 / 확인 필요 / 개선 제안` 순으로 파일·절 참조와 함께 보고한다. 문서를 직접 고치지 않는다.
   - `요약`: 1쪽으로 배경·핵심 문제·비교 결과·위험·권고를 정리한다.
   - `질의 답변`: 직접 답, 근거, 대응 계획, 남은 위험 순으로 쓴다.
   이하 절차는 `신규`·`수정` 기준이다.

1. 읽는다. `STYLE.md` 전체를 읽는다(없으면 `/ai-init` 을 안내하고 멈춘다). `docs/glossary.md` 가 있으면 용어를 따른다. 같은 유형의 기존 문서가 `docs/` 에 있으면 하나 열어 구조의 기준으로 삼는다. 새 구조를 발명하지 않는다. `template_docx` 가 있으면 렌더링 때 그 양식을 쓴다는 것을 리드에 적는다.

2. 문서 리드를 코드·본문 전에 정확히 한 줄로 선언한다.
   `문서: <제목> · 유형 <설계서|검토보고서|가이드|런북|ADR|정의서|회의록|브리프|README|교육> · 독자 <결재권자|개발자|고객|혼합> · 톤 <서술식|경어> · 분량 <n쪽>`
   갈래가 둘이면 질문은 하나만 한다. 정보가 부족해도 초안을 먼저 쓰고 빈 곳은 `[확인 필요]` 로 표시한다. 질문은 최대 3개다.

3. 골격을 잡는다. `references/doc-types.md` 의 유형별 골격을 가져와 내용 없는 절은 통합하거나 지운다. 항상 남는 절은 개요(결론 포함), 본문, 권고/결정, 추가 확인사항이다.

4. 쓰기 직전에 `references/writing-rules-ko.md` 를 읽는다(계획 단계에서는 읽지 않는다). 아키텍처 문서면 `references/arch-doc-types.md`(M1 에 추가)도 읽는다. 규칙 요약: 결론 먼저, 사실/추론/권고 구분, 수치에 출처, 문단 길이 변화, 접속사 남발 금지, 마지막 요약 금지, 비교표 마지막 열은 "검토 의견", 모르는 값은 마커. 구성도는 ` ```diagram ` 블록으로 쓴다(§10.3). 그림을 말로 설명하지 않는다.

5. 파일을 쓴다. `docs/<영역>/<제목>.doc.md`. frontmatter 를 채운다. `date` 는 오늘, `version` 은 0.1, `history` 는 1행.

6. 요청이 있으면 렌더링한다.
   ```bash
   python -m docgen render-docx docs/arch/<제목>.doc.md
   ```
   기본 출력은 `docs/_build/` 다. 제출본은 `--out <경로>`, 회사 양식은 `--template <docx>` 또는 `STYLE.md template_docx` 를 쓴다. `preview` 가 되면 첫 3쪽 PNG 를 보고 표·그림 잘림만 한 번 확인한다. 렌더 오류는 DSL 위반이므로 `.doc.md` 를 고친다. python-docx 를 직접 호출하지 않는다(H10 이 막는다). 렌더링은 M1 에서 docgen 이 준비된 뒤 동작한다.

7. 점검은 `references/preflight-doc.md` 를 한 번 돌리고 한 번에 고치고 끝낸다. 세 번째 패스는 없다. 종료 때 `doc_lint --stop` 이 소프트 룰을 본다.

8. 브리프가 이긴다. 사용자가 특정 표현·이모지·구조를 명시하면 우선한다. 하드 룰에 걸리면 먼저 한 줄로 확인하고, 승인받으면 파일에 마커를 남기고 `STYLE.md` 6절에 기록한다.

## references

- `writing-rules-ko.md`: 문체·표현·비교표. review-report-writer 규칙을 흡수하고 확장했다.
- `doc-types.md`: 유형 10종 골격과 통합 조합, 결론 항목.
- `korean-format.md`: 번호 체계, 날짜·단위·통화·용어 병기, 표·그림 캡션.
- `preflight-doc.md`: 종료 전 점검 목록.

## 하지 않는 것

- 회사명·고객명·금액을 지어내기
- 출처 없는 수치
- 한 문서에 톤 섞기
- 렌더러 우회(python-docx 직접 호출)
- Bash 리다이렉트로 문서 쓰기
