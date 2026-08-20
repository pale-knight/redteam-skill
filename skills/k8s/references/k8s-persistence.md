# Kubernetes-native Persistence

只放 K8s 控制面/工作负载持久化。Node root 后的 SSH/cron/systemd/C2 属于 `/post`。

所有修改必须保存原配置并提供 cleanup。

## 1. ServiceAccount + RoleBinding / ClusterRoleBinding

条件：能创建 SA + binding，或能修改现有 binding。

```bash
kubectl get sa -A
kubectl get rolebinding -A -o yaml > rb-before.yaml
kubectl get clusterrolebinding -o yaml > crb-before.yaml
```

靶场最小验证：创建专用测试 SA，再绑定已存在的目标 role/clusterrole。

```bash
kubectl create serviceaccount redteam-sa -n <NS>
kubectl create rolebinding redteam-test \
  --clusterrole=<ROLE> \
  --serviceaccount=<NS>:redteam-sa \
  -n <NS>
```

如果明确验证 cluster-scoped 权限且有授权：

```bash
kubectl create clusterrolebinding redteam-test \
  --clusterrole=<CLUSTERROLE> \
  --serviceaccount=<NS>:redteam-sa
```

验证 token：

```bash
kubectl create token redteam-sa -n <NS> --duration=10m
```

现代 token 为短期；真正的 persistence 来自 SA + RBAC object，而不是 TokenRequest token 本身。

清理：

```bash
kubectl delete rolebinding redteam-test -n <NS> 2>/dev/null || true
kubectl delete clusterrolebinding redteam-test 2>/dev/null || true
kubectl delete serviceaccount redteam-sa -n <NS>
```

## 2. Workload / Controller Persistence

条件：可创建/更新 Deployment/DaemonSet/CronJob 等。

使用专用、可识别的测试资源，不修改生产 workload：

```text
DaemonSet → 每个/指定 Node 持续 Pod
Deployment → 持续副本
CronJob → 周期执行
```

这类 persistence 仍受 Admission/Pod Security/RBAC 约束。

验证完成删除测试 controller。

## 3. MutatingAdmissionWebhook

条件：能 create/update `mutatingwebhookconfigurations.admissionregistration.k8s.io`，并能提供可被 API Server 访问、TLS 合法的 webhook service/URL。

高影响原因：Mutating webhook 可以修改提交到 API Server 的对象。

Recon：

```bash
kubectl get mutatingwebhookconfigurations -o yaml
kubectl auth can-i create mutatingwebhookconfigurations.admissionregistration.k8s.io
```

在靶场只创建**限定 namespace/object selector 的最小 webhook**验证 mutation，不要默认拦截所有 Pod。

清理：删除测试 webhook configuration 和对应 Service/Deployment/证书。

## 4. MutatingAdmissionPolicy

Kubernetes v1.36 中 `MutatingAdmissionPolicy` / `MutatingAdmissionPolicyBinding` 已为 stable；旧版本可能不存在，因此仍先做版本/API discovery：

```bash
kubectl api-resources | grep -i MutatingAdmission
```

如果资源存在并且 RBAC 可写，视为高影响持久化/策略修改能力。具体 schema 以当前集群 `kubectl explain` 为准：

```bash
kubectl explain mutatingadmissionpolicy --recursive 2>/dev/null | head
```

不要把 v1.36 特性硬套旧集群。

## 5. Existing Workload Modification

如果能 patch 高价值 Deployment/DaemonSet：

```bash
kubectl get deploy <NAME> -n <NS> -o yaml > original.yaml
```

可通过 sidecar/initContainer/image/command/env/volume 等形成持续执行，但生产影响大；优先新建专用测试 workload。若修改，结束：

```bash
kubectl apply -f original.yaml
```

## 6. Control-plane / Shadow API Server

Shadow API Server 属于高级研究型 control-plane persistence，通常要求已经控制 control-plane node/关键证书。托管 EKS/AKS/GKE/ACK control plane 一般不应假设具备该条件。

标记：`RESEARCH / SELF-MANAGED CONTROL-PLANE GATED`。

不作为普通 cluster-admin 的默认路径。

## 7. Detection / Cleanup

```bash
kubectl get events -A --sort-by=.lastTimestamp
kubectl get rolebinding,clusterrolebinding -A
kubectl get mutatingwebhookconfigurations
kubectl get deploy,daemonset,cronjob -A
```

清理所有 `redteam-*` 测试资源并验证 RBAC/Admission 恢复。
