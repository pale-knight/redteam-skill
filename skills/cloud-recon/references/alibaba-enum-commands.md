# Alibaba Cloud / 阿里云枚举速查

阿里云不要只看 OSS。核心身份链是：

```text
RAM User / RAM Role
 → RAM Policy
 → Trust Policy
 → STS AssumeRole
 → ECS / OSS / Function Compute / ACK / 其他服务
```

## 1. CLI / Credential

```bash
aliyun version
aliyun configure list
```

常见凭据：

```text
AccessKeyId + AccessKeySecret
STS: AccessKeyId + AccessKeySecret + SecurityToken
ECS RAM Role
OIDC / CloudSSO / External / CredentialsURI / BearerToken
```

## 2. RAM

```bash
aliyun ram ListUsers
aliyun ram ListRoles
aliyun ram ListPolicies
aliyun ram ListGroups
```

用户：

```bash
aliyun ram GetUser --UserName <USER>
aliyun ram ListPoliciesForUser --UserName <USER>
aliyun ram ListAccessKeys --UserName <USER>
```

Role：

```bash
aliyun ram GetRole --RoleName <ROLE>
aliyun ram ListPoliciesForRole --RoleName <ROLE>
```

重点解析 `AssumeRolePolicyDocument`：

```text
Principal.RAM
sts:AssumeRole
ExternalId
SourceIdentity
跨账户 root/role/user ARN
```

## 3. STS AssumeRole 候选

Recon 阶段可读取 trust 和调用方 policy，形成候选路径；如果需要真正切换身份，交给 `/cloud-attack`。

典型角色 ARN：

```text
acs:ram::<ACCOUNT_ID>:role/<ROLE>
```

## 4. ECS

```bash
aliyun ecs DescribeRegions
aliyun ecs DescribeInstances --RegionId <REGION>
aliyun ecs DescribeSecurityGroups --RegionId <REGION>
aliyun ecs DescribeDisks --RegionId <REGION>
aliyun ecs DescribeSnapshots --RegionId <REGION>
```

重点：InstanceId、VPC/VSwitch、SecurityGroup、公网 IP、镜像、磁盘、RAM Role。

### ECS Metadata

Alibaba ECS IMDS：

```text
http://100.100.100.200/latest/meta-data/
```

普通模式：

```bash
curl -s http://100.100.100.200/latest/meta-data/instance-id
curl -s http://100.100.100.200/latest/meta-data/ram/security-credentials/
```

安全加固模式：

```bash
TOKEN=$(curl -s -X PUT \
  -H 'X-aliyun-ecs-metadata-token-ttl-seconds: 21600' \
  http://100.100.100.200/latest/api/token)

curl -s -H "X-aliyun-ecs-metadata-token: $TOKEN" \
  http://100.100.100.200/latest/meta-data/instance-id
```

Role credential：

```bash
ROLE=$(curl -s -H "X-aliyun-ecs-metadata-token: $TOKEN" \
  http://100.100.100.200/latest/meta-data/ram/security-credentials/)

curl -s -H "X-aliyun-ecs-metadata-token: $TOKEN" \
  "http://100.100.100.200/latest/meta-data/ram/security-credentials/$ROLE"
```

返回应包含 AccessKeyId / AccessKeySecret / SecurityToken / Expiration。

## 5. OSS

```bash
ossutil ls
ossutil ls oss://<BUCKET>
ossutil stat oss://<BUCKET>
```

现代 OSS 重点同时检查：

```text
Bucket ACL
Bucket Policy
Object ACL
Block Public Access
Cross-account principal
IP/VPC conditions
```

需要精确 API 时：

```bash
ossutil api --help
```

不要假设新 Bucket 默认公开；当前新建 Bucket 默认通常是 private，并受 Block Public Access 控制。

## 6. Function Compute

官方 Alibaba CLI REST-style 示例：

```bash
aliyun fc-open GET /2021-04-06/services
aliyun fc-open GET /2021-04-06/services/<SERVICE>/functions
```

重点枚举：

```text
function role
runtime
handler
environment variables
VPC
triggers
HTTP exposure
versions/aliases
```

FC 3.0 / Serverless Devs 环境可按当前控制面工具继续枚举，但先确认版本和工具帮助，不硬套 FC 2.x 参数。

## 7. ActionTrail

```bash
aliyun actiontrail DescribeTrails
aliyun actiontrail LookupEvents --MaxResults 20
```

权限允许时：

```bash
aliyun actiontrail GetAccessKeyLastUsedInfo --AccessKeyId <ACCESS_KEY_ID>
```

## 8. ACK / RRSA 云边界

ACK 的 RRSA 逻辑：

```text
Pod ServiceAccount projected OIDC token
 → AssumeRoleWithOIDC
 → RAM Role
 → STS temporary credentials
```

若当前云身份能获取 ACK 集群认证材料：输出 `/k8s` 候选。
若从 ACK Pod 发现 RRSA RAM Role：输出 `/cloud-recon` 候选。

## 9. Source

- RAM API: https://www.alibabacloud.com/help/en/ram/developer-reference/api-ram-2015-05-01-listusers
- ECS instance RAM roles: https://www.alibabacloud.com/help/en/ecs/user-guide/attach-an-instance-ram-role-to-an-ecs-instance
- ECS metadata: https://www.alibabacloud.com/help/en/doc-detail/49122.htm
- ACK RRSA: https://www.alibabacloud.com/help/en/ack/serverless-kubernetes/user-guide/use-rrsa-to-authorize-pods-to-access-different-cloud-services
- Alibaba CLI advanced credentials: https://www.alibabacloud.com/help/en/cli/other-credentials-oidc-cloudsso-external-credentialsuri-bearertoken
