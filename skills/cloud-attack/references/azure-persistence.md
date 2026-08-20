# Azure / Entra Cloud-native Persistence

## 1. App Password Credential

条件：对目标 App 有新增 credential 的权限。

先列原 credential metadata：

```bash
az ad app credential list --id <APP_ID> -o json > app-creds-original.json
```

新增密码时使用当前 CLI 支持的 append 方式，避免意外替换现有凭据：

```bash
az ad app credential reset \
  --id <APP_ID> \
  --append \
  --display-name redteam-validation
```

记录返回的新 secret（以后无法从 list 重新读取明文）。

验证：使用 App/Service Principal 登录并确认实际权限。

清理：按新增 credential 的 keyId 删除：

```bash
az ad app credential delete --id <APP_ID> --key-id <KEY_ID>
```

## 2. Federated Identity Credential

无长期 client secret 的持久访问路径。

列出：

```bash
az ad app federated-credential list --id <APP_ID>
```

示例 `credential.json`：

```json
{
  "name": "redteam-validation",
  "issuer": "https://token.actions.githubusercontent.com/",
  "subject": "repo:ORG/REPO:environment:Production",
  "audiences": ["api://AzureADTokenExchange"]
}
```

创建：

```bash
az ad app federated-credential create \
  --id <APP_ID> \
  --parameters credential.json
```

清理：

```bash
az ad app federated-credential delete \
  --id <APP_ID> \
  --federated-credential-id redteam-validation
```

## 3. RBAC Assignment Persistence

条件：Owner / User Access Administrator / RBAC Admin 等可以写 role assignments。

```bash
az role assignment create \
  --assignee-object-id <PRINCIPAL_OBJECT_ID> \
  --assignee-principal-type ServicePrincipal \
  --role <ROLE_NAME> \
  --scope <SCOPE>
```

验证后删除新增 assignment。

## 4. App Owner Persistence

如果有权限新增 App owner，新的 owner 可能进一步管理 credential。只在靶场/授权范围验证，记录 owner object id 并在结束时 remove。

## 5. Detection / cleanup

重点审计：

```text
Application credential changes
Federated identity credential changes
Directory role / app owner changes
Azure RBAC role assignment changes
Function/Automation config changes
```
