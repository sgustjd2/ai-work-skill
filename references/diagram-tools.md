# diagram-tools · 다이어그램은 어느 도구로 그리나

docgen 구성도 DSL(` ```diagram ` 블록)과 archify(외부 스킬, 독립 HTML)를 언제 쓰는지 정한다. 색·폰트·회사 사실은 여기 없다. `STYLE.md` 와 테마가 원본이다. archify 자체의 작성 규칙은 설치된 스킬(`~/.claude/skills/archify/SKILL.md`)이 원본이고, 이 문서는 이 저장소에서 그것을 어떻게 쓰는지만 적는다.

## 한 줄 규칙

문서·덱 본문에 들어가는 구성도는 docgen DSL 로 그린다. 문서 밖에서 열어 보고 공유·리뷰하는 다이어그램과 docgen 에 없는 유형(시퀀스·데이터 흐름·상태·워크플로)은 archify 로 그린다.

## 비교

| 항목 | docgen 구성도 DSL | archify | 검토 의견 |
|---|---|---|---|
| 형태 | ` ```diagram ` 블록. docx 에는 PNG, pptx 에는 편집 가능한 도형, md 에는 mermaid | JSON IR 하나가 독립 HTML(SVG 내장, 팬·줌·검색·다크/라이트·내보내기)이 된다 | 결재 문서 안 그림은 DSL, 열어 보는 그림은 archify |
| 유형 | 구성도(컨텍스트·컨테이너·컴포넌트), timeline, chart | architecture, workflow, sequence, dataflow, lifecycle | 시퀀스·상태·파이프라인은 archify 만 된다 |
| 색·폰트 | 회사 테마(`themes/*.json`) | archify 프리셋(기본 classic). 회사 테마가 아니다 | 회사 색이 필요한 자리에는 archify 를 쓰지 않는다 |
| 검증 | 렌더러 경고(노드 20개·그룹 6개 초과) | `validate` 9항목(showcase), `deliver` SHA 영수증, `visual-check`(Chrome 스크린샷) | archify 쪽이 엄격하다. 라벨 겹침을 좌표 단위로 잡는다 |
| 위치 | `.doc.md`/`.deck.md` 안 | 원본 `docs/diagrams/<이름>.<유형>.json`, 결과 `docs/_build/diagrams/<이름>.html` | 원본 JSON 만 커밋한다. HTML 은 `docs/_build/`(gitignore) |
| 쓰는 때 | 설계서 AS-IS/TO-BE, 덱 구성도 장 | 설계 리뷰 세션, API 호출 순서, 비동기 작업 상태, RAG 파이프라인, 위키 공유 | 하나의 그림을 두 도구로 두 번 그리지 않는다 |

## archify 절차

0. 설치 확인. 없으면 `/ai-init --with-archify`(Node 18 이상, 사용자 전역에 한 번).
   ```bash
   node ~/.claude/skills/archify/bin/archify.mjs doctor
   ```
1. 유형을 고른다(위 표). 애매하면 `node ~/.claude/skills/archify/bin/archify.mjs guide "<상황>" --json`.
2. archify 스킬의 절차대로 JSON IR 을 쓴다. 이 저장소에서 더 지키는 것:
   - 파일은 `docs/diagrams/<이름>.<유형>.json`. 본문은 한국어로 쓴다. `meta.locale` 은 생략한다(en·zh-CN 만 지원). 뷰어 UI 가 영어로 남는다는 것을 결과 보고에 한 줄 밝힌다.
   - 노드 종류 대응. DSL `ui` 는 `frontend`, `service` 는 `backend`, `gateway` 는 `backend`(들어오는 연결에 `variant: emphasis`), `data` 는 `database`, `external` 은 `external`, `llm` 은 `backend`(sublabel 에 GPU·모델명).
   - 화살표 라벨은 DSL 과 같은 원칙이다. 프로토콜이나 데이터를 쓰고 동사를 남발하지 않는다. 회사명·고객명·내부 URL 은 `STYLE.md` 정책대로 넣지 않는다.
   - `meta.quality_profile` 은 `showcase`, 주 경로 하나, 노드 12개 이하. `meta.visual_preset`·`subtitle`·`legend` 는 생략한다.
3. 검증하고 전달한다.
   ```bash
   node ~/.claude/skills/archify/bin/archify.mjs validate architecture docs/diagrams/<이름>.architecture.json --quality showcase --json
   node ~/.claude/skills/archify/bin/archify.mjs deliver architecture docs/diagrams/<이름>.architecture.json docs/_build/diagrams/<이름>.html --quality showcase --json
   ```
   라벨 겹침 진단이 나오면 진단이 제시한 값(`labelDy`, `labelDx`, `labelAt`)을 그대로 넣고 다시 검증한다. 한 번에 한 항목만 고친다. 두 번 고쳐도 오류 수가 줄지 않으면 노드나 연결을 줄인다. 종료코드가 0 이 아닌 명령을 성공이라고 쓰지 않는다.
   배치는 세로보다 가로로 넓게 잡는다. 뷰어가 폭에 맞춰 확대하므로 세로로 긴 그림(예: 폭 810·높이 530)은 1440×900 에서 세로로 넘쳐 `visual-check` 가 fail 이 된다. 같은 노드를 폭 1100 이상으로 펼치면 통과한다(골든 10 픽스처).
4. 문서에 넣어야 할 때만 PNG 를 만든다. 두 경로가 있다.
   - 브라우저에서 HTML 을 열고 Export 메뉴의 PNG(뷰어 상태가 제거된 정식 내보내기).
   - Chrome 이 있으면 `visual-check <html> --json` 이 옆에 남기는 `<이름>.visual-check.1440x900.light.png`(뷰어 화면 캡처).
   파일은 `docs/assets/diagrams/<이름>.png` 로 옮기고 `.doc.md` 에 `![그림 n. <제목>](../assets/diagrams/<이름>.png)` 로 넣는다. 캡션 번호는 docgen 규칙을 따른다.
5. 결과 보고에는 HTML 경로, 유형, validate 요약, 영수증 SHA, 브라우저 증거(`visual-check`) 여부, 사람 눈으로 본 검토 여부를 따로 적는다. 셋은 다른 주장이다.

## 하지 않는 것

- archify 로 그린 PNG 를 결재 문서의 유일한 TO-BE 구성도로 쓰기. 색이 회사 테마가 아니다. 본문 구성도는 DSL, archify 는 보조·공유용이다.
- archify JSON 에 스키마에 없는 필드 넣기. 스키마가 `additionalProperties: false` 라 검증에서 막힌다.
- 검증에 실패한 HTML 을 전달하거나, `visual-check` 를 돌리지 않고 "브라우저에서 확인했다" 고 쓰기.
- archify 소스를 저장소나 프로젝트에 복사하기. 설치는 사용자 전역 한 곳이다.
- 같은 그림을 DSL 과 archify 로 두 번 유지하기.
