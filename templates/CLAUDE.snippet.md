## 문서·코드 규약 (ai-work-skill)
- 문서(설계서·보고서·가이드·런북·ADR·브리프)나 덱을 만들기 전에 @STYLE.md 를 읽고 `doc-write` / `deck-write` 스킬 절차를 따른다. 코드 전 한 줄 "문서 리드/덱 리드"를 선언한다.
- 문서는 `.doc.md`/`.deck.md`로 쓰고 docx·pptx는 `docgen`(MCP 또는 `python -m docgen`)으로만 렌더링한다. python-docx/python-pptx를 직접 호출하지 않는다. 색·폰트는 테마 JSON에만 있다.
- em-dash·상투어·이모지·느낌표·가짜 채움(홍길동/TBD)·시크릿은 훅이 차단한다. 차단되면 우회하지 말고 고친다. 모르는 값은 `[확인 필요]`.
- FastAPI 서비스는 `fastapi-service` 골격, CI는 `gitlab-ci` 템플릿, 테스트는 `py-test` 규약, 리뷰는 `py-review` 체크리스트를 따른다. LLM 호출은 LiteLLM 게이트웨이 경유만.
- LiteLLM 설정은 `config_validate` 통과 후에만 배포한다. 키·시크릿은 yaml에 쓰지 않는다.
- 🚫 절대: STYLE.md 무시 · 훅 비활성화 · Bash 리다이렉트로 문서 작성 · 렌더러 우회 · 시크릿 인라인 · 출처 없는 수치
- ⚠️ 먼저 묻기: 예외 마커 추가 · 테마 변경 · MR 코멘트 게시 · 게이트웨이 키 발급/차단 · 파이프라인 재시도
- ✅ 항상: 결론 먼저 · 사실/추론/권고 구분 · 표 마지막 열은 검토 의견 · 렌더 후 미리보기 1회 · 종료 전 preflight
