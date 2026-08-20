# GitOps / Registry / Gitea / Forgejo

---

## 1. Gitea / Forgejo

```bash
# API identity
curl -s http://GITEA:3000/api/v1/user -H "Authorization: token $TOKEN"

# 可见repo
curl -s 'http://GITEA:3000/api/v1/user/repos?limit=50' -H "Authorization: token $TOKEN"
```

重点不是单纯“能读repo”，而是：

```text
repo write/admin
Actions/CI workflow
Deploy keys
Webhooks
Packages/Container Registry
Branch protection
release/token
```

如果 Forgejo/Gitea Actions 或外部 Runner 存在，按 Runner/Workflow 信任链继续。

---

## 2. ArgoCD — GitOps视角

```bash
argocd app list
argocd app get APP
argocd repo list
argocd proj list
```

记录：

```text
Application source repo/path/targetRevision
auto-sync?
Project destination restrictions
repo credentials
cluster destinations
image updater / helm values
```

CI/CD链成功条件之一：从 Repo/ArgoCD 权限出发，使**受控、可回滚的测试变更**被目标 Application 接受/同步。

不要因为底层是 K8s 就中途切；如果已经取得独立 cluster-admin 并准备全面做 RBAC/Node 路径，再由操作者考虑 `/k8s`。

---

## 3. Container / Artifact Registry Poisoning

先证明：

```text
拥有 push/write
+ 下游使用可变tag/版本
+ deploy pipeline会自动消费
```

测试：

```bash
# 使用授权测试tag，不覆盖真实production tag
IMAGE=registry.target.local/app:cicd-proof
# build/push benign marker image
```

### 不能直接下结论的情况

```text
push成功但deployment按digest pin
有provenance/attestation gate
registry写权限只限dev repo
生产需要人工promotion/签名
```

必须观察下游 consumer。

---

## 4. GitOps + Package/Registry链

常见完整链：

```text
Repo write
→ build image/package
→ publish registry
→ GitOps manifest/tag update
→ ArgoCD/Flux sync
→ workload receives controlled build
```

本模块可以把这条交付链走到部署接受；不需要在“进入ArgoCD API”时机械拆模块。
