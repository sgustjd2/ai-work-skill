# vertex · Google Vertex AI 연결

## 인증

서비스 계정 키(JSON)나 워크로드 아이덴티티를 쓴다. `GOOGLE_APPLICATION_CREDENTIALS` 로 키 파일 경로를 주거나, `vertex_credentials` 에 경로를 둔다. 키 내용을 config.yaml 에 붙이지 않는다.

## model_list 항목

```yaml
- model_name: gemini
  litellm_params:
    model: vertex_ai/gemini-3.8-flash
    vertex_project: os.environ/GCP_PROJECT
    vertex_location: global
```

## 모델 ID (2026-09-23 기준)

- Gemini: GA 는 `gemini-3.8-flash`(기본), `gemini-3.5-flash-lite`(대량·저가). Pro 는 `gemini-3.1-pro-preview` 로 아직 미리보기라 운영 기본값으로 두지 않는다. 2.5 세대는 기존 사용자에게만 남아 있다.
- 임베딩: `gemini-embedding-2`(멀티모달)와 `gemini-embedding-001`(텍스트). 두 벡터 공간은 호환되지 않는다.
- Vertex 의 Claude: `vertex_ai/claude-sonnet-5`, `vertex_ai/claude-opus-5-5`. 최신 Claude 도 `global`·`us`·`eu` 위치만 된다.

## 확인할 것

- 프로젝트에 Vertex AI API 가 켜져 있는가. 콘솔 이름이 "Gemini Enterprise Agent Platform" 으로 바뀌었어도 API 와 LiteLLM 접두사(`vertex_ai/`)는 같다.
- 서비스 계정에 `roles/aiplatform.user` 가 있는가.
- 위치(location). Gemini 3.x 와 최신 Claude 는 서울(`asia-northeast3`) 단일 리전에 없다. `global` 은 처리 위치를 보장하지 않으므로 국내 처리가 조건이면 쓸 수 없다.
