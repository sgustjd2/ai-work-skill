# bedrock · AWS Bedrock 연결

## 인증

Bedrock 은 표준 AWS 자격증명 체인을 쓴다. `AWS_ACCESS_KEY_ID`·`AWS_SECRET_ACCESS_KEY`·`AWS_REGION_NAME` 를 환경변수로 두거나, 인스턴스 역할(IAM Role)을 붙인다. 키를 config.yaml 에 쓰지 않는다.

## model_list 항목

`model` 은 `bedrock/<모델 ID 또는 추론 프로파일 ID>` 형식이다. 최신 Claude 는 맨 모델 ID 로 on-demand 호출이 안 되고, `global.`·`us.`·`eu.` 같은 접두사가 붙은 추론 프로파일 ID 를 써야 한다.

```yaml
- model_name: claude
  litellm_params:
    model: bedrock/global.anthropic.claude-sonnet-5
    aws_region_name: ap-northeast-2
```

## 모델 ID (2026-09-23 기준)

| 모델 | 추론 프로파일 ID | 서울(ap-northeast-2) |
|---|---|---|
| Claude Sonnet 5 | `global.anthropic.claude-sonnet-5` | global 프로파일만 |
| Claude Opus 5.5 | `global.anthropic.claude-opus-5-5` | global 프로파일만 |
| Claude Haiku 4.5 | 콘솔에서 확인 | 확인 필요 |

서울에는 `apac.` 지역 프로파일과 리전 내 처리가 없다. global 프로파일은 요청을 다른 리전에서 처리할 수 있다. 지역 프로파일(`us.` 등)은 global 보다 약 10% 비싸다. Sonnet 5.5·Haiku 5.5 가 나오면 ID 만 바꾸고 `model_name` 은 그대로 둔다.

## 확인할 것

- 모델 접근 권한을 Bedrock 콘솔에서 활성화했는가. 활성화 전에는 호출이 거부된다.
- 데이터가 국외 리전에서 처리돼도 되는가. 안 되면 Bedrock 최신 Claude 는 쓸 수 없다. 설계서에 적는다.
- IAM 정책에 `bedrock:InvokeModel` 과 스트리밍용 권한, 추론 프로파일 ARN 이 들어 있는가.
- Bedrock 의 Claude 는 structured outputs·Batch·Files API 가 없다. 구조화 출력을 쓰는 경로의 폴백 대상으로 둘 때는 스키마 검증 후 재시도(genai-patterns)가 있어야 한다.
