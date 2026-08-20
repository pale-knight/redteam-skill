# GCP 枚举速查

## 1. 当前身份 / Project

```bash
gcloud auth list
gcloud config list
gcloud projects list
```

## 2. IAM

```bash
gcloud projects get-iam-policy <PROJECT_ID> --format=json
gcloud iam service-accounts list --project <PROJECT_ID>
gcloud iam service-accounts get-iam-policy <SA_EMAIL>
```

重点权限：

```text
iam.serviceAccounts.actAs
iam.serviceAccounts.getAccessToken
iam.serviceAccountKeys.create
resourcemanager.projects.setIamPolicy
compute.instances.setServiceAccount
cloudfunctions.functions.update
run.services.update
```

## 3. Impersonation 可达性

如果拥有 Token Creator/getAccessToken：

```bash
gcloud auth print-access-token \
  --impersonate-service-account=<SA_EMAIL> >/dev/null
```

成功只代表可以获得该 SA token；继续记录该 SA 的 project/IAM 权限。

## 4. Compute / Storage / Secrets

```bash
gcloud compute instances list --project <PROJECT>
gcloud storage buckets list --project <PROJECT>
gcloud secrets list --project <PROJECT>
gcloud kms keyrings list --location=global --project <PROJECT> 2>/dev/null || true
```

## 5. Serverless

```bash
gcloud functions list --project <PROJECT>
gcloud run services list --project <PROJECT>
```

记录 execution service account / ingress / IAM policy / env references。

## 6. GKE 云侧

```bash
gcloud container clusters list --project <PROJECT>
gcloud container clusters describe <CLUSTER> --location <LOCATION> --project <PROJECT>
```

若可获得 kubeconfig，输出 `/k8s` 为候选下一步。

## 7. Metadata

```bash
curl -s -H 'Metadata-Flavor: Google' \
 http://metadata.google.internal/computeMetadata/v1/project/project-id

curl -s -H 'Metadata-Flavor: Google' \
 http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/
```

## 8. Source

- GCP service account impersonation: https://cloud.google.com/iam/docs/service-account-impersonation
- gcloud: https://cloud.google.com/sdk/gcloud/reference
