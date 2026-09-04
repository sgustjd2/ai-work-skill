# hosts · 다른 에이전트에서 쓰기

이 스킬 세트는 Claude Code 플러그인으로 만들었지만, 표준을 써서 다른 호스트(Codex, Gemini, Grok)에도 붙일 수 있다. 무엇이 어디까지 되는지 정직하게 적는다.

## 무엇이 이식되나

| 층 | 내용 | 이식성 |
|---|---|---|
| MCP 서버 | `docgen`(문서·덱·구성도), `litellm-ops`(게이트웨이 운영·config 검증) | MCP 를 지원하는 어느 호스트에서도 동작. stdio 표준 |
| 스크립트 | `scaffold`·`import_graph`·`test_gaps`·`ci_lint`·`vram_estimate`·`bench_llm`·`doc_lint`·`py_format` | 표준 라이브러리 CLI. 셸에서 바로 실행 |
| 스킬 문서 | `skills/*/SKILL.md` 와 `references/` | 마크다운. 호스트가 지시로 읽는다 |
| 편집 훅 | `doc_lint --pre/--stop`, `py_format --post` | 호스트별. Claude 는 settings.json, 나머지는 pre-commit·CI 로 |

정리하면 MCP 툴과 CLI 는 어디서나 같고, 스킬은 이식 가능한 텍스트다. 호스트에 묶이는 것은 편집 직전 자동 차단(훅)뿐이고, 그 검사도 CI 로 대체할 수 있다.

## 검증 상태

- 확인됨: 이 저장소에서 실제로 실행한 것.
  - Claude Code 경로, 스크립트 전부.
  - **범용 MCP stdio 클라이언트**로 두 서버에 붙어 표준 핸드셰이크(`initialize` → `tools/list` → `tools/call`, 프로토콜 2025-06-18)를 확인했다. 저장소가 아닌 임시 디렉터리에서 절대경로·env 만으로 띄워도 똑같이 붙는다.
  - **Codex CLI 0.153.3 에서 실제 에이전트로 확인했다.** npm 전역 설치 → `codex mcp add` 로 두 서버 등록 → `codex exec` 로 gpt-5.6-luna 가 `docgen/theme_export`(데이타솔루션 토큰 반환)와 `litellm-ops/config_validate`(ok=true, findings 0)를 직접 호출했다. MCP 툴 호출은 승인이 필요해 헤드리스에선 `--approve-for-me` 로 통과시켰다.
- 부분 확인: **Gemini CLI 0.58.0** 도 전역 설치하고 `gemini mcp add -s user` 로 두 서버를 등록해 설정 파일까지 확인했다. 실제 호출은 두 가지가 남는다. (1) Gemini 는 신뢰하지 않은 폴더에서 MCP 를 막으므로 폴더를 신뢰해야 한다. (2) Gemini 로그인(Google 계정 또는 `GEMINI_API_KEY`)이 있어야 에이전트 턴이 돈다. 둘 다 사용자 몫이라 이 세션에서 실행하지 않았다. 서버 명령·프로토콜은 Codex 와 같으므로 로그인 후 같은 방식으로 붙는다.
- Grok · 그 외: MCP 를 지원하면 같은 stdio 명령으로 붙는다. 위 범용 클라이언트가 그 경로를 대신 확인한다.

호스트 CLI 는 버전마다 명령이 바뀐다. 아래 명령은 형식이며, 각 호스트의 최신 문서로 확인한다.

## Claude Code (확인됨)

```bash
claude plugin marketplace add sgustjd2/ai-work-skill
```

그다음 `/plugin install ai-work-skill@ai-work-skill`. 프로젝트에 훅·규약을 넣으려면 `/ai-init`. MCP 는 저장소의 `.mcp.json` 이 `${CLAUDE_PLUGIN_ROOT}` 로 자동 배선한다.

## Codex (확인됨 · 0.153.3)

MCP 서버는 `codex mcp add` 로 등록한다. 이 저장소에서 실제로 실행해 확인했다.

```bash
codex mcp add docgen \
  --env AI_WORK_SKILL_ROOT=E:/workspace/ai-work-skill \
  --env DOCGEN_PROJECT_DIR=E:/workspace/ai-work-skill \
  -- uv run --project E:/workspace/ai-work-skill/mcp/docgen python -m docgen.server

codex mcp add litellm-ops \
  -- uv run --project E:/workspace/ai-work-skill/mcp/litellm_ops python -m litellm_ops.server
```

`codex mcp list` 로 등록을 본다. `uv` 는 PATH 에 있어야 하고, 못 찾으면 절대경로(예: 스쿱 심 `C:/Users/.../scoop/shims/uv.exe`)로 넣는다. `docgen` 은 실행 위치와 무관하게 동작하도록 `AI_WORK_SKILL_ROOT`·`DOCGEN_PROJECT_DIR` 을 저장소 루트로 준다.

MCP 툴 호출은 승인을 요구한다. 대화형에선 그 자리에서 승인하고, 헤드리스(`codex exec`)에선 `--approve-for-me` 로 통과시킨다. 실제로 `codex exec` 에서 gpt-5.6-luna 가 `docgen/theme_export` 와 `litellm-ops/config_validate` 를 호출해 정상 응답을 받았다.

스킬을 텍스트로 쓰려면 저장소 루트의 `.codex-plugin/plugin.json` 과 `AGENTS.md` 를 참조 지시로 읽힌다.

## Gemini CLI (등록 확인됨 · 로그인 필요 · 0.58.0)

`gemini mcp add` 로 등록한다. 이 저장소에서 실행해 설정 파일(`~/.gemini/settings.json`)까지 확인했다.

```bash
gemini mcp add -s user \
  -e AI_WORK_SKILL_ROOT=E:/workspace/ai-work-skill \
  -e DOCGEN_PROJECT_DIR=E:/workspace/ai-work-skill \
  docgen uv run --project E:/workspace/ai-work-skill/mcp/docgen python -m docgen.server

gemini mcp add -s user \
  litellm-ops uv run --project E:/workspace/ai-work-skill/mcp/litellm_ops python -m litellm_ops.server
```

`-s user` 는 폴더가 아니라 사용자 전역에 넣는다. `gemini mcp list` 로 확인한다. 실제 툴 호출까지 가려면 두 가지가 더 필요하다. (1) Gemini 는 신뢰하지 않은 폴더에서 MCP 를 막는다. 그 폴더를 열 때 신뢰하면 풀린다. (2) Gemini 로그인(Google 계정 또는 `GEMINI_API_KEY`). 서버 명령·프로토콜은 Codex 와 같으므로 로그인 후 같은 방식으로 붙는다.

스킬 문서는 `GEMINI.md` 나 컨텍스트 파일로 `skills/` 를 가리켜 참조하게 한다.

## Grok · 그 외 MCP 클라이언트 (문서상)

MCP 를 지원하는 클라이언트라면 위와 같은 stdio 명령을 등록하면 된다. 서버는 호스트를 가리지 않는다. 상대 경로를 쓰면 서버가 기준 디렉터리를 모를 수 있으니, `docgen` 은 `DOCGEN_PROJECT_DIR` 환경변수로 프로젝트 루트를 준다.

```json
{
  "command": "uv",
  "args": ["run", "--project", "/절대경로/ai-work-skill/mcp/docgen", "python", "-m", "docgen.server"],
  "env": { "DOCGEN_PROJECT_DIR": "/절대경로/내-프로젝트" }
}
```

## 스킬을 텍스트로 쓰기

MCP 를 붙이지 않아도 스킬 자체는 마크다운이다. 호스트의 지시 파일(`AGENTS.md`, `GEMINI.md`, 또는 시스템 프롬프트)에서 `skills/<이름>/SKILL.md` 를 읽으라고 가리키면 절차를 따른다. 트리거 어휘는 `skills/llms.txt` 에 있다.

벤더 중립 CLI 배포 도구를 쓰면 스킬만 다른 도구에 넣을 수도 있다.

```bash
npx skills add https://github.com/sgustjd2/ai-work-skill --skill doc-write
```

## 훅을 호스트 없이 걸기

편집 직전 자동 차단은 Claude Code 기능이다. 다른 호스트에서는 같은 검사를 커밋·CI 에 건다.

```bash
# git pre-commit 훅 예시
python templates/doc_lint.py --all docs skills README.md
python templates/py_format.py --post   # ruff 있으면 포맷
```

CI 는 `.github/workflows/ci.yml` 이 `doc_lint --all` 을 이미 돌린다. 호스트가 무엇이든 커밋된 결과는 같은 검사를 받는다.

## 스크립트만 쓰기

스킬·MCP 없이 스크립트만 써도 된다. 전부 표준 라이브러리 CLI 다.

```bash
python skills/fastapi-service/scripts/scaffold.py --name svc --target ./svc --with-sse
python skills/py-refactor/scripts/import_graph.py svc
uv run --project mcp/litellm_ops python -m litellm_ops config-validate config.yaml
uv run --project mcp/docgen python -m docgen render-docx docs/설계서.doc.md
```
