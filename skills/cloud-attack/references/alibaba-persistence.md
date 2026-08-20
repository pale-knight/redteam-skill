# Alibaba Cloud / 阿里云平台原生持久化

主机 SSH/cron/systemd/C2 属于 `/post`；ACK RBAC/Webhook 属于 `/k8s`。

## 1. RAM User AccessKey

条件：`ram:CreateAccessKey` on controlled/high-value RAM user。

```bash
aliyun ram ListAccessKeys --UserName <USER>
aliyun ram CreateAccessKey --UserName <USER>
```

成功：创建响应返回新的 AccessKeyId/AccessKeySecret。

清理：

```bash
aliyun ram DeleteAccessKey \
  --UserName <USER> \
  --UserAccessKeyId <ACCESS_KEY_ID>
```

## 2. RAM Role Trust Persistence

保存：

```bash
aliyun ram GetRole --RoleName <ROLE> > role-original.json
```

新增受控 Principal 到 trust：

```bash
aliyun ram UpdateRole \
  --RoleName <ROLE> \
  --NewAssumeRolePolicyDocument "$(cat trust-test.json)"
```

验证：使用受控 principal `aliyun sts AssumeRole ...`。

清理：恢复原 `AssumeRolePolicyDocument`。

## 3. RAM Policy Attachment / Version

对已有受控 User/Role 增加 policy，或创建新的 policy version 并切 default，都能形成持续控制能力。

要求：保存原 attachment/default version，测试结束恢复。

## 4. Function Compute Persistence

如果可持续修改 Function code/config/trigger 或绑定/控制其 RAM Role，可以形成 Serverless persistence。

必须记录：

```text
原 code/version
原 handler/runtime
原 environment
原 role
原 triggers
```

验证完成恢复。

## 5. CloudSSO / OIDC / Federation

Alibaba CLI/SDK 当前支持 OIDC、CloudSSO、External、CredentialsURI、BearerToken 等高级 credential 方法。若环境本身使用 federation，枚举信任关系和可控 IdP/subject 比只找长期 AK 更重要。

只有在明确具备创建/修改 federation 配置的权限时才执行 persistence 验证；否则记录为候选路径。

## 6. Detection / Cleanup

关注 ActionTrail 中：

```text
CreateAccessKey / DeleteAccessKey
UpdateRole
AttachPolicy* / DetachPolicy*
CreatePolicyVersion / SetDefaultPolicyVersion
Function Compute configuration/code/trigger changes
```
