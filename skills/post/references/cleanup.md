# 收工与痕迹

> **TECH：** 撤掉本场投放物  
> **成功：** persist 对象查询不到、payload 不在、暂存 loot 已删  
> **默认不做：** `wevtutil cl Security`、清空 `auth.log`（这本身是最响告警）

每条持久化的精确删除命令以 `persistence-*.md` 的 RESTORE 为准。本文件给顺序。

---

## 顺序

```text
1. C2：把 sleep 拉长或 kill beacon；操作机停对目标的 listener 暴露
2. 持久化 RESTORE（任务/服务/Run/WMI/key/cron/systemd）
3. 删 payload、dll、shellcode 文件
4. 删暂存 loot.zip / collect/
5. 可选：只删本场相关日志条目（操作者确认）
6. 默认跳过整卷清日志
```

---

## 投放物

```cmd
schtasks /delete /tn "<LookLikeTask>" /f
sc stop <SvcName> & sc delete <SvcName>
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v <Name> /f
del /f /q C:\Windows\Temp\payload.exe C:\Users\Public\loot.zip
```

```bash
systemctl disable --now sync-time.service
rm -f /etc/systemd/system/sync-time.service
systemctl daemon-reload
crontab -l   # 编辑删行
sed -i '/ssh-ed25519 AAAA/d' ~/.ssh/authorized_keys
rm -f /usr/local/bin/update /tmp/loot.zip
```

WMI：用 persistence-windows.md 的三段 Remove-WmiObject。

验证：query 失败/不存在、`ps` 无 implant、authorized_keys 无操作者公钥。

---

## 日志（非默认）

操作者 **明确要求** 再做。优先按时间/Event ID/用户删本场条目，不要整卷。

Windows 整卷（IMPACT：Security 突然空）：

```cmd
wevtutil cl Security
wevtutil cl System
wevtutil cl "Windows PowerShell"
```

Linux 整卷（同样响）：

```bash
: > /var/log/auth.log
: > /var/log/wtmp
history -c; unset HISTFILE
```

RDP 记录：

```cmd
reg delete "HKCU\Software\Microsoft\Terminal Server Client\Default" /va /f
```

时间戳：

```cmd
powershell (Get-Item file.exe).LastWriteTime = '2024-01-01 12:00:00'
```

```bash
touch -t 202401011200 file
```

改之前记下原时间，授权报告要能对上。

---

## notes 收工段

```text
removed: task/svc/key/files
left behind: (必须诚实写没删掉的)
logs: untouched | selective | wiped (IMPACT)
C2: beacon killed / listener still up for others
```
