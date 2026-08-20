# Azure / Entra ID 枚举速查

## 1. Tenant

```bash
curl -s https://login.microsoftonline.com/<DOMAIN>/.well-known/openid-configuration | jq .issuer
az account show
az account list --all -o table
```

Azure CLI 现代用户认证可能强制 MFA；自动化优先使用已有 token、Service Principal、Managed Identity 或 workload identity，不把 ROPC/用户名密码作为默认。

## 2. Entra

```bash
roadrecon auth
roadrecon gather
roadrecon gui
```

AzureHound：

```bash
./azurehound list --tenant <TENANT_ID> -o azure.json
```

重点：

```text
Global Administrator / Privileged Role Administrator
Application Administrator / Cloud Application Administrator
App owners
Service principals
App roles / OAuth permissions
Federated credentials
Managed identities
```

## 3. ARM / RBAC

```bash
az group list -o table
az resource list -o table
az role assignment list --all -o table
az role definition list -o table
az identity list -o table
az vm list -d -o table
az keyvault list -o table
az functionapp list -o table
az webapp list -o table
```

## 4. Applications / Credentials

```bash
az ad app list --all
az ad sp list --all
az ad app owner list --id <APP_ID>
az ad app credential list --id <APP_ID>
az ad app federated-credential list --id <APP_ID>
```

这里只枚举 metadata；新增 credential 属于 `/cloud-attack`。

## 5. Managed Identity

VM 内：

```bash
curl -s -H 'Metadata: true' \
 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/' | jq
```

记录：client_id / object_id / resource scope / token expiry。

## 6. AKS 云侧

```bash
az aks list -o table
az aks show -g <RG> -n <CLUSTER>
```

如果当前身份可获得集群认证材料，输出 `/k8s` 候选，不继续 K8s 利用。

## 7. Source

- Azure CLI: https://learn.microsoft.com/cli/azure/
- Federated credentials: https://learn.microsoft.com/cli/azure/ad/app/federated-credential
