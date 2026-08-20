# Cloud ↔ Kubernetes 身份边界

这里只处理“云身份与 K8s 身份之间的转换线索”。K8s RBAC、Pod、Secret、escape 交给 `/k8s`；云 IAM/RAM 权限交给 `/cloud-recon`/`/cloud-attack`。

## AWS / EKS

Pod 内：

```bash
env | grep -E '^AWS_(ROLE_ARN|WEB_IDENTITY_TOKEN_FILE|CONTAINER_CREDENTIALS_)'
aws sts get-caller-identity
```

可能是：

```text
IRSA
EKS Pod Identity
Node instance role fallback
```

发现 AWS Role 后：记录 ARN、token source、有效期。候选下一步 `/cloud-recon`。

云侧获得 EKS API credential 后：候选 `/k8s`。

## Azure / AKS

检查：

```bash
env | grep -Ei 'AZURE_|FEDERATED|IDENTITY'
```

常见：

```text
Microsoft Entra Workload Identity
Managed Identity
legacy AAD Pod Identity
```

取得 Azure token 后只确认 principal/resource scope，再由操作者决定是否 `/cloud-recon`。

## GCP / GKE

检查 metadata / workload identity：

```bash
curl -s -H 'Metadata-Flavor: Google' \
 http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/
```

获得 GCP SA identity → 候选 `/cloud-recon`。

## Alibaba / ACK

RRSA：

```bash
env | grep -Ei 'ALIBABA|ALICLOUD|OIDC|ROLE_ARN'
find /var/run /var/run/secrets -type f 2>/dev/null | grep -Ei 'oidc|token|rrsa'
```

概念链：

```text
K8s ServiceAccount
 → projected OIDC token
 → STS AssumeRoleWithOIDC
 → RAM Role
```

ACK 会自动续期短期 OIDC token；不要把 token 文件当永久凭据。

## 输出

```text
来源：Pod / Cloud CLI / Metadata
K8s identity：namespace/serviceaccount
Cloud identity：Role/SA/Managed Identity
Credential type：projected OIDC / STS / metadata token
Expiration：...
Candidate: 继续当前模块 / /cloud-recon / /k8s
```

**由操作者选择，不自动切换。**
