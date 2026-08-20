# AWS IAM Attack Graph / 权限关系分析

目标：把“某个 Action 存在”升级成“当前 Principal 最终能到达哪些身份/权限”。

## 1. PMapper

安装：

```bash
pip install principalmapper
```

创建图：

```bash
pmapper --profile target graph create
```

常用查询：

```bash
pmapper --profile target query 'who can do iam:CreateUser'
pmapper --account <ACCOUNT_ID> query -s 'preset privesc *'
pmapper --account <ACCOUNT_ID> visualize --filetype svg
```

重点看：

```text
当前 User/Role
 → AssumeRole
 → PassRole
 → service identity
 → policy modification
 → Admin / target action
```

PMapper 图是候选路径，不代表每条路径都可直接利用；仍需验证 Condition、region、service constraints、resource policy、SCP/permission boundary/session policy。

## 2. Cloudsplaining

```bash
cloudsplaining download --profile target
cloudsplaining create-exclusions-file
cloudsplaining scan --exclusions-file exclusions.yml --input-file target.json
```

单策略：

```bash
cloudsplaining scan-policy-file --input-file policy.json
```

关注：

```text
Privilege Escalation
Credential Exposure
Data Exfiltration
Infrastructure Modification
Wildcard Resource/Action
```

## 3. 手工 Trust Graph

对高价值 Role：

```bash
aws iam get-role --role-name <ROLE>
```

分别判断：

```text
A. Caller 是否允许 sts:AssumeRole 到该 ARN
B. Target trust 是否允许 Caller / Account / Federated Principal
C. Condition 是否满足
D. Permission Boundary / SCP / Session Policy 是否削弱最终权限
```

## 4. 输出格式

```text
Principal: arn:...
Path:
  principal A
  -> sts:AssumeRole role B
  -> iam:PassRole role C to Lambda
  -> role C can perform X

已确认：A/B
待验证：C/D
建议：/cloud-attack 中验证最短、影响最大的路径
```

## 5. Source

- PMapper: https://github.com/nccgroup/PMapper
- Cloudsplaining: https://github.com/salesforce/cloudsplaining
