# gitlab-mcp-playbook · GitLab MCP 연결과 파이프라인 진단

## 연결

GitLab 인스턴스의 MCP 엔드포인트를 Claude Code 에 붙인다.

```
claude mcp add --transport http gitlab https://<gitlab-host>/api/v4/mcp
```

또는 프로젝트 `.mcp.json` 에 `gitlab` 항목을 둔다(`/ai-init` 이 넣는다). 인증은 Claude Code 에서 `/mcp` 를 눌러 브라우저로 승인한다.

전제: 인스턴스가 18.3 이상(19.2부터 Free 티어), GitLab Duo 와 beta 기능이 켜져 있어야 한다. 안 되면 커뮤니티 서버 `@zereight/mcp-gitlab` 를 개인 액세스 토큰(`GITLAB_PERSONAL_ACCESS_TOKEN`)으로 stdio 연결한다.

## 툴 이름

공식 이름을 먼저 시도하고, 없으면 목록에서 가까운 이름을 고른다. 이름을 코드에 하드코딩하지 않는다.

- MR 조회: `get_merge_request`, `get_merge_request_diffs`, `list_merge_requests`.
- MR 쓰기: `save_note`, `save_merge_request_review`(사용자 승인 후).
- 파이프라인: `get_pipeline`, `get_pipeline_jobs`, `get_job`(트레이스 포함), `save_pipeline`(retry·cancel).
- 파일·커밋: `get_repository_file`, `add_commit`.

## 파이프라인 실패 진단 순서

1. `get_pipeline` 으로 어느 스테이지·잡이 실패했는지 본다.
2. 실패한 잡의 `get_job` 으로 트레이스(로그)를 읽는다.
3. 원인을 세 가지로 나눈다.
   - 코드: 테스트·린트 실패. 소스를 고친다.
   - 환경: 의존성·버전·캐시. lock 파일과 이미지 태그를 확인한다.
   - 인프라: 러너·레지스트리·권한. 러너 태그와 CI 변수 접근을 확인한다.
4. 고친 뒤 재시도는 사용자 확인을 받고 `save_pipeline` 으로 retry 한다.

## 코멘트·리뷰 게시

리뷰나 노트는 사용자가 승인했을 때만 `save_note`·`save_merge_request_review` 로 올린다. 승인 없이 게시하지 않는다.
