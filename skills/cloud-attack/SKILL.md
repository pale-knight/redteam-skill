---
name: cloud-attack
description: "Cloud control-plane exploitation for AWS, Azure/Entra, GCP, and Alibaba Cloud: IAM/RAM privilege escalation, impersonation, cross-account trust, serverless/compute control, and cloud-native persistence. Host OS persistence/C2 after root/SYSTEM belongs to /post. K8s RBAC belongs to /k8s. Operator chooses next modules; new identities default to /cloud-recon first."
---

# /cloud-attack — 云控制面利用

> **scope：** 已有云身份，打到 **更高云身份 / 账户控制 / 能下发 OS 执行的 compute**。改策略前保存原文 + rollback。平台原生持久化在这里；主机 SSH/C2 → `/post`；K8s RBAC → `/k8s`。

厂商命令在 reference。先看是哪朵云、再看是提权还是持久化，**只 Read 那一份**。禁止把 AWS+Azure+GCP+阿里八个文件开局全读。

- AWS：`references/aws-privesc-paths.md` / `references/aws-serverless.md` / `references/aws-persistence.md`
- Azure：`references/azure-privesc-paths.md` / `references/azure-persistence.md`
- GCP：`references/gcp-privesc-paths.md` / `references/gcp-persistence.md`
- 阿里：`references/alibaba-privesc-paths.md` / `references/alibaba-persistence.md`

CVE 仅 versioned 组件 → `../shared/cve-enrichment.md`。IAM/SCP 不是 CVE。

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

## 0. 成功 / 强度

AssumeRole、改 trust、改 Lambda 代码、建联合凭据都是攻击原语，不是只读验证。先 snapshot 再改。

**不算：** 只列出 AdministratorAccess、只 pmapper 出图。

---

## 0.5 EDR

IAM/SCP/Conditional Access/SG = 本模块。  
SSM/RunCommand **已经在 OS 执行** 被 AV 杀 → `/edr-bypass` → 回来把云→host 链打完。

---

## 1. 决策树

```text
手上是哪朵云 + 当前 principal 能做什么（来自 /cloud-recon）
        ↓
AssumeRole / actAs / 改 trust / 附加策略     → references/*-privesc-paths.md
PassRole + 建计算 / 改 serverless 代码        → serverless / compute 节
能下发 VM/SSM                                 → 执行后候选 /post 或继续云
能拿 EKS/AKS/GKE/ACK kubeconfig               → 停，候选 /k8s
要平台持久化                                  → references/*-persistence.md
身份已经变了                                  → 候选 /cloud-recon 再枚举新身份
```

不要按 AWS→Azure→GCP→阿里把四本手册跑完。

---

## 2. 原语（指针）

**提权：** CreatePolicyVersion / Attach*Policy / UpdateAssumeRolePolicy / PassRole+create / SA impersonation / RAM UpdateRole。

**Serverless/Compute：** Lambda UpdateFunctionCode、FC 改代码、EC2+实例配置、元数据 Role。拿到 OS shell 后本链可停，候选 `/post`。

**持久化：** AccessKey、Role trust、联邦凭据、Lambda Layer。SA key 是否允许创建看组织策略。

**K8s 边界：** 只拿到集群凭证就出 `/k8s`，不要在这打 RBAC。

---

## 3. 完成后

写入 `./notes.md`。候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`（默认不要再 `/cloud-attack`）。
