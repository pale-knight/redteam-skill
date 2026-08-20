# Azure / Entra 提权路径

## 1. ARM RBAC

高价值角色：

```text
Owner
User Access Administrator
Role Based Access Control Administrator
Managed Identity Operator
Contributor + 可组合的 identity assignment 权限
```

```bash
az role assignment list --all -o table
az role definition list -o table
```

如果拥有 role assignment 写权限，可将受控 principal 赋予测试范围内目标角色。保存现有 assignment，验证后删除新增 assignment。

## 2. Application / Service Principal Ownership

如果对高权 App 有 Owner 或相应 Directory 权限，可新增 app credential / federated credential，获得 App 权限。

持久化操作 → `azure-persistence.md`。

## 3. Managed Identity

VM/App/Function 内取得 MI token：

```bash
curl -s -H 'Metadata: true' \
 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/'
```

然后枚举其 ARM RBAC / Key Vault / Automation / resource access。

## 4. Key Vault

先判断 Key Vault 是 RBAC 模式还是 legacy access policy。

```bash
az keyvault show -n <VAULT>
az keyvault secret list --vault-name <VAULT>
```

仅在确认授权与读取权限后取目标 secret。

## 5. Automation / Function / Web App

高权限 Automation Account 或 Function App 修改权限可能导致代码以 Managed Identity/应用身份运行。

先保存：runbook/function deployment/config/identity，再做最小验证，最后恢复。

## 6. Entra Hybrid

AAD/Entra Connect：需要对应服务器访问和授权；同步账户/云同步配置可能形成 on-prem ↔ cloud 高价值路径。

PRT：只在明确的已控 Entra-joined endpoint 和授权范围内处理。

## 7. AKS boundary

如果 Azure 控制面权限可获得 AKS kubeconfig，仅报告 `/k8s` 候选，不在此文件继续 RBAC。
