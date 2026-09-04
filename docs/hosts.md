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

- 확인됨: 이 저장소에서 실제로 실행한 것. MCP 서버 두 개의 툴 노출, 스크립트 전부, Claude Code 경로.
- 문서상: 각 호스트 문서가 지원한다고 밝힌 것. Codex·Gemini·Grok 의 MCP·스킬 연결 방식은 문서상이며 이 세션에서 실행하지 않았다.

호스트 CLI 는 버전마다 명령이 바뀐다. 아래 명령은 형식이며, 각 호스트의 최신 문서로 확인한다.

## Claude Code (확인됨)

```bash
claude plugin marketplace add sgustjd2/ai-work-skill
```

그다음 `/plugin install ai-work-skill@ai-work-skill`. 프로젝트에 훅·규약을 넣으려면 `/ai-init`. MCP 는 저장소의 `.mcp.json` 이 `${CLAUDE_PLUGIN_ROOT}` 로 자동 배선한다.

## Codex (문서상)

저장소 루트에 `.codex-plugin/plugin.json` 과 `AGENTS.md` 를 두었다. Codex 는 스킬을 `$<이름>` 으로 부른다.

```bash
codex plugin marketplace add sgustjd2/ai-work-skill
```

등록과 설치는 별개 단계다. 등록 뒤 호스트 UI 에서 설치·활성화한다. MCP 는 Codex 설정(`config.toml`)에 넣는다.

```toml
[mcp_servers.docgen]
command = "uv"
args = ["run", "--project", "/절대경로/ai-work-skill/mcp/docgen", "python", "-m", "docgen.server"]

[mcp_servers.litellm-ops]
command = "uv"
args = ["run", "--project", "/절대경로/ai-work-skill/mcp/litellm_ops", "python", "-m", "litellm_ops.server"]
```

## Gemini CLI (문서상)

Gemini CLI 는 MCP 서버를 설정 파일의 `mcpServers` 에 넣는다. Claude 의 `.mcp.json` 과 형식이 비슷하되 `${CLAUDE_PLUGIN_ROOT}` 대신 절대경로를 쓴다.

```json
{
  "mcpServers": {
    "docgen": {
      "command": "uv",
      "args": ["run", "--project", "/절대경로/ai-work-skill/mcp/docgen", "python", "-m", "docgen.server"]
    }
  }
}
```

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
