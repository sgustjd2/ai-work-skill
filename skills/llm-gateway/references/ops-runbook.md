# ops-runbook · 게이트웨이 운영

각 절차는 litellm-ops MCP 툴이나 `python -m litellm_ops` CLI 로 한다.

## 기동

1. `config.yaml` 을 `config_validate` 로 검사한다. 오류 0 을 확인한다.
2. `docker compose up -d`. postgres 가 먼저 떠야 한다.
3. `gateway_health` 로 준비를 확인하고 `test_completion` 으로 모델 하나에 실제 응답을 받는다.

## 모델 추가

1. `config.yaml` 의 `model_list` 에 항목을 더한다. 키는 `os.environ/` 참조로.
2. `.env` 에 환경변수를 더한다. `config_validate` 로 V5(환경변수 누락)를 확인한다.
3. 재기동하고 `list_models` 로 등록을 확인한다. 폴백 대상이면 `test_completion` 으로 응답 형식을 본다.

## 키 회전

1. 새 키를 `key_create` 로 발급한다. 전체 키를 비밀 저장소에 넣는다.
2. 서비스 설정을 새 키로 바꾸고 배포한다.
3. 옛 키를 `key_block` 으로 차단한다. 문제가 없으면 나중에 삭제한다.

## 장애 진단 순서

1. `gateway_health`: 생존·준비와 죽은 엔드포인트를 본다.
2. 죽은 엔드포인트가 있으면 폴백이 동작하는지 `test_completion` 으로 확인한다.
3. 제공자 상태 페이지를 본다. 리전 장애면 이중화 리전으로 트래픽이 가는지 확인한다.
4. 특정 키만 실패하면 `key_info` 로 예산 소진·차단 여부를 본다.
5. 전반적으로 느리면 레이트 리밋과 동시성, 데이터베이스 연결을 본다.

## 업그레이드

이미지 태그를 올리기 전에 릴리스 노트를 본다. config 스키마 변경이 있으면 `config_validate` 로 먼저 확인한다. 스테이징에서 `test_completion` 과 폴백을 확인한 뒤 운영에 올린다.
