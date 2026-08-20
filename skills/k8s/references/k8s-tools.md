# Kubernetes / Container 工具

## kubectl

```bash
kubectl auth whoami 2>/dev/null || true
kubectl auth can-i --list
kubectl get pods -A -o wide
kubectl get role,rolebinding -A
kubectl get clusterrole,clusterrolebinding
```

TokenRequest：

```bash
kubectl create token <SERVICEACCOUNT> -n <NS> --duration=10m
```

## KubeHound

```bash
wget https://github.com/DataDog/KubeHound/releases/latest/download/kubehound-$(uname -o | sed 's/GNU\///g')-$(uname -m) -O kubehound
chmod +x kubehound
export KUBECONFIG=/path/to/kubeconfig
./kubehound
```

要求当前发行版对应的 Docker/Docker Compose 环境。按启动输出访问图数据库/Jupyter。

## badPods

```bash
git clone https://github.com/BishopFox/badPods
cd badPods
```

不要直接批量 apply；先根据当前 RBAC + Pod Security/Admission 条件选对应 manifest。

风险类型：

```text
privileged
hostPID
hostIPC
hostNetwork
hostPath
```

## kubeletctl

```bash
kubeletctl scan --cidr <CIDR>
kubeletctl pods -s <NODE_IP>
```

具体参数以当前版本 `kubeletctl --help` 为准。

## peirates

```bash
./peirates
```

适合 Pod 内快速枚举与攻击候选。任何修改型 action 先审查命令。

## kube-hunter

```bash
kube-hunter --remote <CLUSTER_IP>
```

偏发现暴露面；不要把扫描结果直接当可利用结论。

## CDK

容器内安全评估工具，适合检查 capabilities、socket、mount、kernel/runtime 等条件。使用当前 release 并复核结果。

## etcdctl

```bash
ETCDCTL_API=3 etcdctl endpoint health --endpoints=<ENDPOINT>
ETCDCTL_API=3 etcdctl get /registry/ --prefix --keys-only
```

## Sources

- KubeHound: https://github.com/DataDog/KubeHound
- badPods: https://github.com/BishopFox/badPods
- Kubernetes SA TokenRequest: https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/
