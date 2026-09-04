---
name: gitlab-ci
description: >
  GitLab CI/CD 파이프라인을 만들고 고치고 운영한다. ".gitlab-ci.yml", "파이프라인", "CI 만들어줘",
  "빌드/배포 자동화", "컨테이너 레지스트리", "MR 파이프라인", "환경별 배포(dev/stg/prod)", "파이프라인 실패 원인",
  "잡 로그 확인", "MR 템플릿", "브랜치 전략" 요청에 반드시 쓴다. GitLab 공식 MCP(연결돼 있으면)로 파이프라인·잡·MR 을
  조회하고 재시도한다. GitHub Actions·Jenkins 는 대상이 아니다.
version: 0.1.0
user-invocable: true
argument-hint: "[생성 | 진단 <pipeline id|MR> | 배포 대상]"
allowed-tools:
  - Bash(python */skills/gitlab-ci/scripts/ci_lint.py *)
  - Bash(git *)
  - mcp__gitlab
---

# gitlab-ci

GitLab CI/CD 를 만들고 고친다. 파이프라인 조각은 `assets/` 와 `references/` 가 원본이다.

## 절차

1. 프로젝트 성격을 본다. Python 인가, Docker 를 쓰는가, 배포 대상이 무엇인가.

2. 파이프라인 리드를 한 줄로 선언한다.
   `CI: <프로젝트> · 스테이지 <lint,test,build,scan,deploy> · 배포 <compose 호스트|k8s|ACA|ECS|Cloud Run|없음> · 게이트 <dev 자동, stg/prod 수동>`

3. `assets/gitlab-ci.yml` 을 복사하고 변수만 채운다. 새로 발명하지 않는다. 배포 잡의 script 는 `references/deploy-targets.md` 의 대상별 블록으로 교체한다.

4. 검증한다.
   ```
   python skills/gitlab-ci/scripts/ci_lint.py .gitlab-ci.yml
   ```
   `GITLAB_URL`·`GITLAB_TOKEN`·`CI_PROJECT_ID` 가 있으면 GitLab CI Lint API 로 정식 검사하고, 없으면 로컬 구조 검사를 한다.

5. MR·이슈 템플릿과 CODEOWNERS 를 추가한다(`assets/`). 이미 있으면 건너뛴다.

6. 진단 요청이면 `references/gitlab-mcp-playbook.md` 순서를 따른다. 파이프라인 조회, 실패 잡 로그, 원인 3분류(코드·환경·인프라), 수정, 재시도(사용자 확인 후).

## references

- `deploy-targets.md`: compose·Kubernetes·Azure Container Apps·AWS ECS·Cloud Run 배포 블록.
- `pipeline-recipes.md`: 모노레포 changes, 캐시·아티팩트, 스케줄, 러너 태그, 시크릿.
- `gitlab-mcp-playbook.md`: MCP 연결·툴 이름·진단 순서.
- `branching.md`: 트렁크 기반 전략과 MR 규칙.

## 하지 않는 것

- 시크릿을 `.gitlab-ci.yml` 에 직접 쓰기.
- 승인 없이 파이프라인 재시도·MR 코멘트 게시.
- GitHub Actions·Jenkins 설정.
