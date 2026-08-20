# Memory Execution / Injection

不要默认：

```text
VirtualAllocEx → WriteProcessMemory → CreateRemoteThread
```

这条链在现代 EDR 上高度相关。根据 observed blocker 换 primitive。

成功：原先在内存/线程阶段被拦的 payload，现在跑到预期代码路径。然后回原 Attack 模块拿 shell/权限。

---

## 1. 先看拦在哪

```text
新 RWX 分配被拦            → 改 image-backed / RX 后写 / 先 RW 再 RX
WriteProcessMemory 被拦     → 用 NtWriteVirtualMemory syscall / section map
CreateRemoteThread 被拦     → APC / callback / 入口劫持 / 无新线程
执行后几秒被杀              → 内存扫描 / sleep 加密 / Caro-Kann 时序
```

---

## 2. Module stomping / image-backed

用已加载合法模块的 image-backed 区承载代码，减少匿名 RWX。

流程见 `process-execution.md`。注意：模块完整性、call-stack provenance 仍可能告警。

---

## 3. Entry Point Hijacking

```text
CREATE_SUSPENDED
→ 找目标 image 入口
→ 写入 stub / 改入口
→ ResumeThread
```

减少显式 remote thread。

---

## 4. Callback / APC / threadless

```c
EnumWindows((WNDENUMPROC)payload, 0);
QueueUserAPC((PAPCFUNC)payload, hThread, 0);
```

APC 目标线程必须能进入 alertable wait。Early Bird：挂起进程的主线程在 Resume 后第一次 alertable 时跑。

Threadless / 不新建线程的方案：覆盖合法函数入口或用回调。实现跟具体 PoC 走，不要现场发明。

---

## 5. Caro-Kann（memory-scan timing research）

官方思路：

```text
加密 payload 放在 RW
小 RX stub 先执行（扫描打在良性 stub 上）
delay
解密
RW→RX
跳到 payload
```

```bash
git clone https://github.com/S3cur3Th1sSh1t/Caro-Kann.git
cd Caro-Kann
# 交叉编译依赖以项目 README 为准
make
```

标为 **research / 环境门控**。不是通用注入替代。成功标准仍然是：原被拦 payload 现在执行。

---

## 6. 权限与目标进程

```text
注入其他进程：需要合适句柄权限，PPL 目标先看 credential-access-evasion / kernel
当前进程 self-inject：遥测通常更低，钓鱼/Web 落地优先 self-exec
```

远程注入被拦时，先改成当前进程执行（钓鱼 ClickFix、Web 的 dropper），不要死磕 lsass/csrss。

---

## 7. 成功判断

```text
Before: 同 payload 在内存/线程阶段被拦
After : payload 到达预期函数/回连
Cleanup: 结束测试进程；不要 stomped 系统进程长期运行
Resume: 原 Attack 模块
```
