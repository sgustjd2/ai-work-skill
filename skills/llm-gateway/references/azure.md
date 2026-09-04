# azure · Azure OpenAI 연결

## 필요한 값

- 리소스 엔드포인트: `https://<리소스>.openai.azure.com`. `AZURE_API_BASE_*` 로 둔다.
- API 키: `AZURE_API_KEY_*`. 배포(deployment)마다 리소스가 다르면 키도 다르다.
- `api_version`: 예 `2024-08-01-preview`. 기능에 따라 버전을 맞춘다.

## model_list 항목

`model` 은 `azure/<배포명>` 형식이다. 배포명은 Azure 포털에서 만든 이름이지 모델 이름이 아니다.

```yaml
- model_name: gpt-4o
  litellm_params:
    model: azure/gpt-4o
    api_base: os.environ/AZURE_API_BASE_KR
    api_key: os.environ/AZURE_API_KEY_KR
    api_version: "2024-08-01-preview"
```

## 리전 이중화

같은 `model_name` 으로 두 리전을 등록하면 게이트웨이가 로드밸런싱하고, 한 리전 장애를 다른 리전이 흡수한다. 리전마다 `api_base`·`api_key` 를 다르게 둔다. 한국 서비스는 Korea Central 을 기본으로, 다른 리전을 이중화로 둔다.

## 임베딩

`text-embedding-3-small` 도 배포로 만들어 같은 방식으로 등록한다. RAG 서비스가 이 `model_name` 을 쓴다.
