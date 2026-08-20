---
name: k8s
description: "Kubernetes and container exploitation: identity/RBAC, secrets, kubelet/etcd, managed-cloud workload identities, container-to-node escape including CVE-2026-31431 Copy Fail, and Kubernetes-native persistence. Use when already in a Pod/container or holding kubeconfig. Own the chain to cluster-admin, node root, or a usable cloud identity. Operator chooses next modules. Endpoint blocks after OS execution hand off to /edr-bypass then return."
---

# /k8s — Kubernetes / Container 攻击

> **scope：** 已在 Pod/Container 内或已有 Kubernetes API 凭据，打到 **cluster-admin / node root / 可用云身份**。K8s-native 持久化留本模块。▸ 云身份默认不要 `/cloud-attack`。候选只认 `~/.claude/skills/shared/modules.yaml`（`modules.py tail`）。

本模块是红队攻击模块。RBAC / badPods / 逃逸 / Copy Fail 门控满足就打。Admission/RBAC 拒绝不是 EDR。

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
Pod / kubeconfig
        ↓
身份 + can-i
        ↓
当前选中的 K8s 链（RBAC / Secret / 逃逸 / 云身份 / 平台持久化）
        ↓
cluster-admin 或 node root 或可验云身份
        ↓
/k8s COMPLETE
```

**不算：** 只 `kubectl get pods`、只 KubeHound 出图、只看到 SA token。

---

## 0.4 CVE

先拆 **精确组件版本**（kubelet / runtime / kernel / CNI），再 Read `../shared/cve-enrichment.md`。不要搜 “Kubernetes” dump 全部洞。Managed 看厂商 backport。

```bash
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.nodeInfo.kubeletVersion}{"\t"}{.status.nodeInfo.containerRuntimeVersion}{"\t"}{.status.nodeInfo.kernelVersion}{"\n"}{end}'
uname -r
```

---

## 0.5 EDR

RBAC / Admission / PSA / seccomp / OPA = **本模块**。  
只有 container/node **已经在 OS 执行** 被 workload EDR 杀 → `/edr-bypass` → 回 `/k8s` 把链打完。

`kubectl exec Forbidden`、privileged 被 Admission 拒 = 不是 EDR。

---

## 1. 决策树

```text
cat token/namespace + kubectl auth whoami + can-i --list
        ↓
A. 能 create pods/controllers 或 bind RBAC
      → Read references/rbac-abuse.md → 打到更高身份或 node
B. 能 get secrets / create token
      → 本模块取证、换成可用身份，再回到 A 或云身份
C. privileged / hostPath / docker.sock / hostPID / 危险 cap
      → Read references/container-escape.md → node root
D. 同节点共享镜像层 + kernel 门控
      → Copy Fail：Read container-escape.md（不要当通杀）
E. IRSA / Azure WI / GKE WI / ACK RRSA 环境变量或 projected token
      → Read references/cloud-identity.md → 校验 sts/az，候选 /cloud-recon
F. kubelet 匿名/nodes/proxy 或 etcd 暴露
      → Read references/k8s-tools.md 对应节
G. 要平台持久化
      → Read references/k8s-persistence.md
H. 以上都弱
      → 版本指纹 → cve-enrichment → 有公开 PoC 再打
```

同一条链打穿再换。不要按课表把 A–H 全跑一遍。

---

## 2. 静默身份（本 SKILL 仅保留这组）

```bash
SA=/var/run/secrets/kubernetes.io/serviceaccount
cat "$SA/namespace" 2>/dev/null
kubectl auth whoami 2>/dev/null
kubectl auth can-i --list
kubectl config current-context
```

现代 projected token 会过期，不要当永久 Secret。更多客户端/图 → 需要时再 Read `references/k8s-tools.md`（含 KubeHound）。

`list` 被拒就逐项 `can-i`，不要停。

---

## 3. 分支（命令在对应 reference）

**RBAC / 建工作负载：** 高价值不只是 `pods/create`（exec、ephemeral、secrets、token、webhook、controller）。→ `references/rbac-abuse.md`

**逃逸：** socket / privileged / hostPath / hostPID / cap / kubelet cred / 版本门控 CVE。docker.sock 在**这台 Linux**上逃到 host 也可走 `/privesc-linux`（操作者选）。集群内跨 Pod → 本模块。→ `references/container-escape.md`

**云身份：** token ≠ admin。校验后再候选 `/cloud-recon`，不要在这里做 IAM 提权。→ `references/cloud-identity.md`

**持久化：** SA+binding、DaemonSet、Admission Webhook。SSH/cron/C2 → `/post`。→ `references/k8s-persistence.md`

---

## 4. 完成后

```text
身份 / 是否 cluster-admin / 是否 node root
云身份线索：
RESTORE: 删的 Pod/binding/webhook
```

写入 `./notes.md`。候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。
