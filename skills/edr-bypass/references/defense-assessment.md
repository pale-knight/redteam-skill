# Defense Assessment — 先定位阻断层

本文件只做判断。判断完立刻进对应技术文件动手，不要停在“建议换马”。

---

## 1. 必填输入

```text
Originating module:
Blocked action (exact):
OS / build / arch:
Privilege / integrity:
EDR product (if known):
What happened:
  file disappeared / toast / process killed / exit 0xC0000428 /
  AMSI / AppLocker 8004 / PPL 0x5 / hang
```

---

## 2. 分层探针（低影响 → 高影响）

### 2.1 落地

```powershell
# 写一个无害 marker
Set-Content C:\Windows\Temp\rt-marker.txt 'rt'
Get-Content C:\Windows\Temp\rt-marker.txt
```

被删/隔离 → 静态扫描 / 写拦截 → `static-payload.md`

### 2.2 进程创建

```cmd
cmd.exe /c whoami > C:\Windows\Temp\rt-whoami.txt
```

cmd 被拦、谁ami 没文件 → 进程创建 / 命令行 → `process-execution.md` + `native-api-syscalls.md`

### 2.3 脚本

```powershell
powershell -NoP -C "whoami"
```

PS 被拦但 cmd 可以 → AMSI/CLM/脚本规则 → `script-runtime.md` 或 `application-control.md`

### 2.4 内存

原 payload 落地成功、进程起来、几秒内被杀 → 内存扫描 / 行为链 → `memory-execution.md` + `callstack-telemetry.md`

### 2.5 应用控制

Event Viewer：

```powershell
Get-WinEvent -LogName 'Microsoft-Windows-AppLocker/EXE and DLL' -MaxEvents 20
Get-WinEvent -LogName 'Microsoft-Windows-Windows Defender/Operational' -MaxEvents 20
```

8004 / CI 3077 → `application-control.md`

### 2.6 PPL / 内核

对 lsass 的 OpenProcess 返回 ACCESS_DENIED，或驱动加载 577/5771 → `credential-access-evasion.md` / `kernel-edr.md`

---

## 3. 产品指纹（有就记，没有也继续）

```powershell
Get-Service | ? { $_.Name -match 'CSFalcon|Sentinel|Cylance|CbDefense|elastic|WinDefend|Sense' }
Get-Process | ? { $_.Name -match 'MsMpEng|CSFalcon|Sentinel|elastic|CrowdStrike' }
```

产品名用来选已知绕过，**不是**“没识别就不能打”。未知 EDR 仍按阻断层打。

---

## 4. 路由

```text
静态/落地          → static-payload.md
AMSI/脚本          → script-runtime.md
进程树/命令行/hook → process-execution.md + native-api-syscalls.md
内存/注入          → memory-execution.md
调用栈/sleep       → callstack-telemetry.md
WDAC/AppLocker     → application-control.md
PPL/驱动/EDR 进程  → kernel-edr.md
凭据 dump 被拦     → credential-access-evasion.md
```

输出一句给操作者：

```text
Layer: AMSI
Next file: script-runtime.md
Then resume: /phishing ClickFix callback
```
