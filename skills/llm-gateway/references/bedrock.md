# bedrock · AWS Bedrock 연결

## 인증

Bedrock 은 표준 AWS 자격증명 체인을 쓴다. `AWS_ACCESS_KEY_ID`·`AWS_SECRET_ACCESS_KEY`·`AWS_REGION_NAME` 를 환경변수로 두거나, 인스턴스 역할(IAM Role)을 붙인다. 키를 config.yaml 에 쓰지 않는다.

## model_list 항목

`model` 은 `bedrock/<모델 ID>` 형식이다. 모델 ID 는 리전마다 제공 여부가 다르다.

```yaml
- model_name: claude-sonnet
  litellm_params:
    model: bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
    aws_region_name: us-east-1
```

## 확인할 것

- 모델 접근 권한을 Bedrock 콘솔에서 활성화했는가. 활성화 전에는 호출이 거부된다.
- 리전에 해당 모델이 있는가. 없으면 다른 리전을 쓰거나 크로스 리전 추론을 켠다.
- IAM 정책에 `bedrock:InvokeModel` 과 스트리밍용 권한이 있는가.
