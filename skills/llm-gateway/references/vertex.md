# vertex · Google Vertex AI 연결

## 인증

서비스 계정 키(JSON)나 워크로드 아이덴티티를 쓴다. `GOOGLE_APPLICATION_CREDENTIALS` 로 키 파일 경로를 주거나, `vertex_credentials` 에 경로를 둔다. 키 내용을 config.yaml 에 붙이지 않는다.

## model_list 항목

```yaml
- model_name: gemini
  litellm_params:
    model: vertex_ai/gemini-1.5-pro
    vertex_project: os.environ/GCP_PROJECT
    vertex_location: us-central1
```

## 확인할 것

- 프로젝트에 Vertex AI API 가 켜져 있는가.
- 서비스 계정에 `roles/aiplatform.user` 가 있는가.
- 위치(location)에 모델이 제공되는가. 지역에 따라 다르다.
