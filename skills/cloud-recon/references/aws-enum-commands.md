# AWS 枚举命令速查

## 1. 当前身份

```bash
aws --profile target sts get-caller-identity
aws --profile target configure list
```

## 2. IAM

```bash
aws --profile target iam list-users
aws --profile target iam list-roles
aws --profile target iam list-groups
aws --profile target iam list-policies --scope Local

aws --profile target iam get-user --user-name <USER>
aws --profile target iam list-attached-user-policies --user-name <USER>
aws --profile target iam list-user-policies --user-name <USER>
aws --profile target iam get-user-policy --user-name <USER> --policy-name <POLICY>

aws --profile target iam get-role --role-name <ROLE>
aws --profile target iam list-attached-role-policies --role-name <ROLE>
aws --profile target iam list-role-policies --role-name <ROLE>
aws --profile target iam get-role-policy --role-name <ROLE> --policy-name <POLICY>
```

### Trust Policy 重点

`get-role` 返回的 `AssumeRolePolicyDocument` 是目标 Role 的信任策略。记录：

```text
Principal
Action
Condition
ExternalId
aws:PrincipalArn
aws:PrincipalOrgID
sts:SourceIdentity
```

跨账户 `AssumeRole` 通常同时要求：

```text
调用方 identity policy 允许 sts:AssumeRole
+
目标 Role trust policy 信任调用方
+
Condition 满足
```

## 3. IAM permission discovery

```bash
enumerate-iam --access-key <AK> --secret-key <SK>
```

Pacu：

```text
Pacu> import_keys target
Pacu> run iam__bruteforce_permissions
Pacu> run iam__enum_roles
```

## 4. EC2

```bash
aws --profile target ec2 describe-regions --all-regions
aws --profile target ec2 describe-instances --region <REGION>
aws --profile target ec2 describe-security-groups --region <REGION>
aws --profile target ec2 describe-volumes --region <REGION>
aws --profile target ec2 describe-snapshots --owner-ids self --region <REGION>
aws --profile target ec2 describe-instance-profile-associations --region <REGION>
```

记录 instance profile / IAM role。

## 5. S3

```bash
aws --profile target s3api list-buckets
aws --profile target s3api get-bucket-location --bucket <BUCKET>
aws --profile target s3api get-bucket-acl --bucket <BUCKET>
aws --profile target s3api get-bucket-policy --bucket <BUCKET>
aws --profile target s3api get-public-access-block --bucket <BUCKET>
```

公开枚举：

```bash
aws s3 ls s3://<BUCKET> --no-sign-request
```

## 6. Lambda / Serverless

```bash
aws --profile target lambda list-functions --region <REGION>
aws --profile target lambda get-function --function-name <FUNC> --region <REGION>
aws --profile target lambda get-function-configuration --function-name <FUNC> --region <REGION>
aws --profile target lambda list-layers --region <REGION>
aws --profile target lambda list-layer-versions --layer-name <LAYER> --region <REGION>
aws --profile target lambda get-policy --function-name <FUNC> --region <REGION>
aws --profile target lambda get-function-url-config --function-name <FUNC> --region <REGION> 2>/dev/null || true
```

重点：execution role、layers、extensions、environment、resource policy、URL auth。

## 7. Secrets / SSM / KMS

```bash
aws --profile target secretsmanager list-secrets --region <REGION>
aws --profile target ssm describe-parameters --region <REGION>
aws --profile target kms list-keys --region <REGION>
aws --profile target kms list-aliases --region <REGION>
```

Recon 阶段先列元数据；读取 secret/value 视授权范围和任务目标决定。

## 8. EKS 云侧

```bash
aws --profile target eks list-clusters --region <REGION>
aws --profile target eks describe-cluster --name <CLUSTER> --region <REGION>
aws --profile target eks list-access-entries --cluster-name <CLUSTER> --region <REGION> 2>/dev/null || true
```

如果能获得 K8s API 凭据：记录为候选 `/k8s`，不在本文件执行 RBAC 利用。

## 9. Source

- AWS IAM Roles / trust policies: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html
- AWS CLI: https://docs.aws.amazon.com/cli/latest/reference/
