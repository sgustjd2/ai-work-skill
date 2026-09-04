# deploy-targets · 배포 대상별 스크립트

`.gitlab-ci.yml` 의 `.deploy` 잡 script 를 대상에 맞는 블록으로 교체한다. 필요한 CI 변수는 프로젝트 설정에 masked·protected 로 둔다.

## compose 호스트 (ssh)

원격 호스트에서 새 이미지를 받아 재기동한다.

필요 변수: `DEPLOY_HOST`, `DEPLOY_USER`, `SSH_PRIVATE_KEY`(파일 형식).

```yaml
script:
  - eval $(ssh-agent -s)
  - chmod 600 "$SSH_PRIVATE_KEY" && ssh-add "$SSH_PRIVATE_KEY"
  - ssh -o StrictHostKeyChecking=accept-new "$DEPLOY_USER@$DEPLOY_HOST"
      "cd /srv/app && docker compose pull && docker compose up -d"
```

## Kubernetes (Helm)

필요 변수: `KUBE_CONFIG`(파일), `RELEASE`, `NAMESPACE`.

```yaml
image: alpine/helm:3
script:
  - export KUBECONFIG="$KUBE_CONFIG"
  - helm upgrade --install "$RELEASE" ./chart -n "$NAMESPACE"
      --set image.tag="$CI_COMMIT_SHORT_SHA" --wait
```

## Azure Container Apps

필요 변수: `AZURE_CREDENTIALS`, `ACA_APP`, `ACA_RG`.

```yaml
image: mcr.microsoft.com/azure-cli
script:
  - az login --service-principal -u "$AZ_CLIENT_ID" -p "$AZ_CLIENT_SECRET" --tenant "$AZ_TENANT"
  - az containerapp update -n "$ACA_APP" -g "$ACA_RG"
      --image "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

## AWS ECS

필요 변수: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `ECS_CLUSTER`, `ECS_SERVICE`.

```yaml
image: amazon/aws-cli
script:
  - aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" --force-new-deployment
```

## Google Cloud Run

필요 변수: `GCP_SA_KEY`, `GCP_PROJECT`, `CLOUD_RUN_SERVICE`, `GCP_REGION`.

```yaml
image: google/cloud-sdk:slim
script:
  - echo "$GCP_SA_KEY" | gcloud auth activate-service-account --key-file=-
  - gcloud run deploy "$CLOUD_RUN_SERVICE" --project "$GCP_PROJECT" --region "$GCP_REGION"
      --image "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" --quiet
```
