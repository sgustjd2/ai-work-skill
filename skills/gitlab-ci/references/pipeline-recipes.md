# pipeline-recipes · 파이프라인 조각

## 모노레포에서 바뀐 곳만

`rules:changes` 로 특정 경로가 바뀐 MR 에서만 잡을 돌린다.

```yaml
test:api:
  rules:
    - changes: [services/api/**/*]
```

## 캐시와 아티팩트

- 캐시는 잡 사이 재사용(uv·의존성). 키를 `uv.lock` 파일 해시로 잡는다.
- 아티팩트는 잡 결과 전달(리포트·빌드 산출물). `expire_in` 을 짧게 둔다.
- 둘을 헷갈리지 않는다. 캐시는 없어도 되고, 아티팩트는 다음 잡이 필요로 한다.

## 스케줄 파이프라인

야간 보안 스캔·의존성 점검은 스케줄로 돌린다.

```yaml
nightly_scan:
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

## 러너 태그

무거운 빌드는 전용 러너로 보낸다.

```yaml
build:
  tags: [docker, large]
```

## 시크릿

- CI 변수는 masked·protected 로 둔다. 로그에 찍히지 않게 한다.
- protected 변수는 protected 브랜치·태그에서만 노출된다. prod 배포 변수를 여기 둔다.
- 값을 `.gitlab-ci.yml` 에 직접 쓰지 않는다.
