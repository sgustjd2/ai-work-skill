# azure · Azure OpenAI 연결

## 필요한 값

- 리소스 엔드포인트: `https://<리소스>.openai.azure.com`. `AZURE_API_BASE_*` 로 둔다.
- API 키: `AZURE_API_KEY_*`. 배포(deployment)마다 리소스가 다르면 키도 다르다.
- `api_version`: `"v1"`. Azure 의 v1 API 가 GA 라서 날짜형 버전(`2024-08-01-preview` 같은 것)을 달마다 올리지 않아도 된다. LiteLLM 은 `"v1"` 을 받으면 `/openai/v1/` 경로로 호출한다(2026-09-23 기준 소스로 확인, 공식 문서 예시는 아직 날짜형). 미리보기 기능이 꼭 필요할 때만 날짜형 버전을 쓴다.

## model_list 항목

`model` 은 `azure/<배포명>` 형식이다. 배포명은 Azure 포털에서 만든 이름이지 모델 이름이 아니다. 아래 예시는 배포명을 모델명과 같게 만든 경우다. `model_name` 은 앱이 부르는 용도 별칭이라 모델을 바꿔도 그대로 둔다.

```yaml
- model_name: chat
  litellm_params:
    model: azure/gpt-6-sol
    api_base: os.environ/AZURE_API_BASE_KR
    api_key: os.environ/AZURE_API_KEY_KR
    api_version: "v1"
```

## 모델 고르기 (2026-09-23 기준)

- `gpt-6-sol`: 기본값. 가격 대비 성능이 균형이다.
- `gpt-6-astra`: 가장 어려운 추론·코딩. 단가가 Sol 의 다섯 배라 `chat-hard` 같은 별도 별칭으로 둔다.
- `gpt-6-luna`: 분류·추출·라우팅처럼 쉬운 대량 작업.
- `o3`·`o4-mini`·`gpt-5` 날짜 스냅샷은 2026-10~12 에 종료된다. 남아 있으면 옮긴다.

모델 ID 와 종료일은 자주 바뀐다. 배포 전에 Azure 모델 목록과 OpenAI 종료 공지를 다시 본다.

## 리전과 데이터 위치

같은 `model_name` 으로 두 리전을 등록하면 게이트웨이가 로드밸런싱하고, 한 리전 장애를 다른 리전이 흡수한다. 리전마다 `api_base`·`api_key` 를 다르게 둔다. 한국 서비스는 Korea Central 을 기본으로, 다른 리전을 이중화로 둔다.

배포 유형이 데이터 처리 위치를 정한다. Korea Central 에서 최신 GPT 는 Global Standard 배포로만 나온다(처리가 해외에서 일어날 수 있다). 국내 처리가 계약 조건이면 Standard 배포를 써야 하는데, 2026-09-23 기준 Korea Central Standard 에는 GPT 가 없고 `text-embedding-3-large` 만 있다. 고객 데이터가 들어가는 서비스는 설계서에 배포 유형을 적는다.

## 임베딩

`text-embedding-3-small`·`text-embedding-3-large` 가 현행이다. 배포로 만들어 같은 방식으로 등록한다. RAG 서비스가 이 `model_name` 을 쓴다. 임베딩 모델을 바꾸면 기존 벡터와 호환되지 않으니 전량 재임베딩을 계획한다.
