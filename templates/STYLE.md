---
ai_work_skill: 0.1
org: 데이타솔루션 기술연구소
lang: ko
theme: datasolution
template_pptx: null
template_docx: null
office_font: 맑은 고딕
tone_doc: 서술식
tone_deck: 개조식
date_format: "YYYY-MM-DD"
currency: 원
numbering: "1.1"
placeholder_marker: "[확인 필요]"
filename_pattern: "{title}_v{version}_{date:%Y%m%d}"
render_output_dir: docs/_build
services: []
dash_policy: deny
emoji_policy: deny
exclaim_policy: deny
buzzword_policy: block
allow_terms: []
glossary: docs/glossary.md
---

# 문서 스타일 가이드

이 파일은 사람이 읽는 문서 계약이자 `doc_lint` 훅의 설정 파일이다. 위 frontmatter 는 기계가 읽고, 아래 6개 절은 사람이 읽는다. 값을 바꾸면 문서·덱 렌더링과 훅 검사가 함께 바뀐다. 색·폰트·치수의 실제 값은 테마 JSON(`themes/<theme>.json` 또는 `docs/theme.json`)에만 있다.

## 1. 조직과 독자

- 이 프로젝트가 만드는 서비스: [확인 필요]
- 문서를 읽는 사람: 결재권자(비개발자)와 개발자. 결재권자는 첫 화면에서 결론과 비용, 일정을 찾는다. 개발자는 인터페이스와 구성도를 찾는다.
- 두 독자가 3초 안에 찾는 것을 문서 맨 앞에 둔다.
- `services` 목록은 트렌드 브리프의 관련도 판단과 설계서 AS-IS 참조에 쓴다.

## 2. 문서 유형과 톤

- 유형별 골격과 톤은 `doc-write` 스킬의 `references/doc-types.md` 를 따른다.
- 보고서·설계서 본문은 `tone_doc`(기본 서술식, ~다). 고객 대상 문서만 경어(~습니다).
- 덱은 `tone_deck`(기본 개조식). 슬라이드마다 헤드 메시지 한 개, 명사형 종결.

## 3. 표기 규칙

- 번호 체계: `numbering`(기본 1.1). 날짜: `date_format`(기본 YYYY-MM-DD). 통화: `currency`.
- 용어 병기는 첫 등장 1회만 `한글(영문)`. 이후에는 한글만.
- 고유명사와 제품명은 공식 표기를 쓴다. 표준·금지 표기는 `docs/glossary.md` 표에 모은다.
- 한 문서 안에서 존댓말과 평서문을 섞지 않는다.

## 4. 구조 규칙

- 결론을 먼저 쓴다. 사실은 단정문, 추론은 "~로 예상된다", 권고는 "~하는 것이 적절하다" 로 구분한다.
- 대안이 둘 이상이면 비교표를 만들고 마지막 열은 "검토 의견"(판단)으로 채운다.
- 모르는 값은 `placeholder_marker`(기본 [확인 필요])로 표시하고 "추가 확인사항" 절에 모은다.
- 마지막 문단은 앞 내용을 반복하는 요약이 아니라 다음 행동(누가, 언제, 무엇을)으로 끝낸다.

## 5. 시각 규칙

- 테마: `theme`. 색과 폰트, 치수는 테마 JSON 에만 있다. 문서·덱 어디에도 색 값을 직접 쓰지 않는다.
- 표 캡션은 표 위에 `[표 n]`, 그림 캡션은 그림 아래에 `[그림 n]`.
- 구성도 노드는 6종(ui, service, gateway, data, external, llm), 덱 레이아웃은 10종을 쓴다.
- 로고는 `docs/assets/logo.png` 가 있을 때만 표지 좌상단에 넣는다.

## 6. 금지와 허용 예외

- 프로젝트 추가 금지: [확인 필요]
- 하드 룰 예외가 필요하면 아래 표에 기록하고 파일에 마커를 남긴다. 시크릿(H9)은 예외가 없다.

| 규칙 | 파일 | 이유 | 승인자 | 날짜 |
|---|---|---|---|---|
