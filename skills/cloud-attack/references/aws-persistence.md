# AWS Cloud-native Persistence

平台原生持久化留在 `/cloud-attack`。主机 SSH/cron/systemd/C2 不写在这里。

所有变更：**先保存原状态 → 创建最小验证 → 验证 → 清理/恢复。**

## 1. IAM User / AccessKey

条件：`iam:CreateUser` / `iam:CreateAccessKey` / policy attachment 权限。

```bash
aws iam create-user --user-name <REDTEAM_USER>
aws iam create-access-key --user-name <REDTEAM_USER>
```

不要默认附加 AdministratorAccess；根据授权目标附加最小验证 policy。

清理：

```bash
aws iam delete-access-key --user-name <REDTEAM_USER> --access-key-id <AKIA...>
# detach/delete inline policies first
aws iam delete-user --user-name <REDTEAM_USER>
```

## 2. Existing User AccessKey

条件：`iam:CreateAccessKey` on existing user。

```bash
aws iam list-access-keys --user-name <USER>
aws iam create-access-key --user-name <USER>
```

成功即得到新的长期 AccessKey；记录创建时间和 key id。

清理：delete-access-key。

## 3. Role Trust Policy Persistence

条件：`iam:UpdateAssumeRolePolicy`。

保存：

```bash
aws iam get-role --role-name <ROLE> \
  --query 'Role.AssumeRolePolicyDocument' > role-trust-original.json
```

准备仅增加测试 Principal 的 trust JSON，然后：

```bash
aws iam update-assume-role-policy \
  --role-name <ROLE> \
  --policy-document file://role-trust-test.json
```

验证：从被信任 Principal 执行 `sts assume-role`。

清理：

```bash
aws iam update-assume-role-policy \
  --role-name <ROLE> \
  --policy-document file://role-trust-original.json
```

## 4. Policy Persistence

可以通过：

```text
CreatePolicyVersion + SetDefault
AttachRolePolicy / AttachUserPolicy
PutRolePolicy / PutUserPolicy
```

建立后续云控制权限。每条都必须记录原 attached policies/default version 以便恢复。

## 5. STS GetFederationToken — 临时存活窗口

这不是永久持久化。

条件：使用 IAM User 长期凭据调用；AssumedRole 等临时凭据不能作为该 API 的默认调用来源。

```bash
aws sts get-federation-token \
  --name redteam-session \
  --duration-seconds 129600
```

最长可到 36 小时（受调用身份/策略限制）。它用于研究“原长期 key 被撤销后，已签发临时 session 的生命周期”，不要称为永久后门。

## 6. Lambda Layer / Extension Persistence

见 `aws-serverless.md`。

保存原 Layers，添加 extension layer，验证函数运行，再恢复原 Layers 和删除测试 layer version。

## 7. Detection / Cleanup

关注 CloudTrail：

```text
CreateUser / CreateAccessKey
Attach*Policy / Put*Policy
CreatePolicyVersion / SetDefaultPolicyVersion
UpdateAssumeRolePolicy
UpdateFunctionConfiguration / PublishLayerVersion
```

持久化验证完成后恢复。
