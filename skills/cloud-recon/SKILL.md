---
name: cloud-recon
description: "Cloud control-plane reconnaissance for AWS, Azure/Entra, GCP, and Alibaba Cloud: identity, IAM/RAM, trust, resources, metadata, and managed-Kubernetes cloud-side boundary. Recon only — no policy changes, no privilege escalation. Operator may select /cloud-attack or /k8s."
---

# /cloud-recon — 云控制面信息收集

> **scope：** 已有云凭据或云环境线索后，只读枚举身份、权限、信任、资源。不改策略、不建用户、不更新函数。▸ 高价值路径交给操作者选 `/cloud-attack` 或 `/k8s`。

命令全书在 reference，**不要在 SKILL 复制四朵云 CLI**。

- AWS：`references/aws-enum-commands.md` + `references/aws-iam-graph.md`
- Azure：`references/azure-enum-commands.md`
- GCP：`references/gcp-enum-commands.md`
- 阿里云：`references/alibaba-enum-commands.md`
- 云↔K8s：`references/cloud-k8s-identity.md`
- versioned 软件 CVE：`../shared/cve-enrichment.md`

---

## 开局与收尾

开局第一件事：Read `./notes.md`。没有则 `python ~/.claude/skills/bin/notes.py init`。只按已拿下/凭据继续。
走到哪条链，才 Read **一份** `references/<file>.md`。禁止开局全读、禁止凭记忆写 payload。
监听 / sudo / 输密码 / Permission denied：立刻停，说明等操作者做什么，等回报。不要假装已成功。
收尾：
1. 追加 `./notes.md`
2. `python ~/.claude/skills/bin/modules.py tail <本模块名>`
   Read 备用：`~/.claude/skills/shared/modules.yaml`
   禁止 `./modules.yaml` 和 `python ../bin/...`
3. 优先 `default_next`；`never_default` 不得当作默认（操作者点名除外）
4. 名册外的名字不许建议
5. 停。等操作者选 `/模块` 或 `/clear`
`/edr-bypass` 半条链未完：打通后回本模块，不要 /clear。


---

## 0. 成功条件

```text
平台 / Account / Tenant / Project
当前 principal 与凭据类型（长期 / STS / MI / SA / OIDC）
有效权限与高价值 trust（AssumeRole / actAs / Owner）
资源面摘要（计算 / 存储 / serverless / 密钥）
托管 K8s 是否可拿 kubeconfig（只报告，不进集群）
```

**禁止：** 建 AccessKey、改 Trust、更新 Lambda、写 Bucket Policy。

IAM 误配 **不是 CVE**。只有自管 appliance/DB 引擎/镜像才走 enrichment。

---

## 1. 决策树（按手上材料，不按厂商课表）

```text
还不知道哪朵云     → DNS/ASN/泄露变量识别平台
AWS 密钥/STS       → references/aws-enum-commands.md + pmapper
Azure token/SP/MI  → references/azure-enum-commands.md + ROADtools
GCP SA JSON/ADC    → references/gcp-enum-commands.md
阿里 AK/STS/RRSA   → references/alibaba-enum-commands.md
只有 VM 内         → 元数据（§4）再当新身份重新枚举
能 get 集群凭证    → 停，候选 /k8s
```

一次做完当前身份的图，不要 AWS 命令抄完再无脑把 Azure 全书跑一遍。

---

## 2. 平台识别

```text
amazonaws.com / azurewebsites.net / run.app / aliyuncs.com
AWS_ACCESS_KEY_ID / AZURE_CLIENT_SECRET / GOOGLE_APPLICATION_CREDENTIALS
ALIBABA_CLOUD_ACCESS_KEY_ID
```

---

## 3. 每朵云（指针）

**AWS：** `sts get-caller-identity` → IAM/trust/resource policy → pmapper/cloudsplaining → EC2/S3/Lambda/Secrets。EKS 只 `list/describe-cluster`，能拿 API 就候选 `/k8s`。

**Azure：** `az account show` / roadrecon / AzureHound。MFA 用户不要默认 `az login -u -p`。AKS 能出 kubeconfig → `/k8s`。

**GCP：** `gcloud auth list` + IAM policy + SA impersonation **探测**（能 print-token 只记可达身份，不在 recon 里提权利用）。GKE 同上。

**阿里云：** RAM/STS/ECS/OSS/FC/ActionTrail/ACK。元数据 `100.100.100.200`（含 token 模式）。ACK RRSA → 记 RAM 身份，候选 `/k8s` 或继续本模块枚举该 Role。

---

## 4. 元数据

```text
AWS 169.254.169.254     Azure 169.254.169.254
GCE metadata.google.internal
阿里 100.100.100.200
EKS IRSA / AKS WI / GKE WI / ACK RRSA
```

token ≠ admin。记下 principal 再枚举。

---

## 5. 完成后

写入 `./notes.md`。候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。只建议，不自动跳。
