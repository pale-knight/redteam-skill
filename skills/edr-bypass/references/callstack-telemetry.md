# Call Stack / Sleep / Telemetry

EDR 证据来自 unwind、sleeping 明文、返回地址不在 ntdll 时使用。

Syscall 解决不了这一层。direct syscall 往往让栈 **更差**。

---

## 1. 现象

```text
payload 能跑，sleep 期间被扫到
调用栈显示返回地址在 unbacked / 非 ntdll 区域
间接 syscall 仍告警 call-stack spoofing 不完整
```

---

## 2. Sleep 加密

休眠前加密 payload 内存，醒来再解密。

```bash
git clone https://github.com/Cracked5pider/Ekko.git
# Ekko: CreateTimerQueueTimer ROP 链
# Foliage: APC-based
# Cronos: Nt APC
```

Beacon/Sliver/Havoc 若自带 sleep mask，先开自带的，不要叠三套。

```text
Sliver: generate ... --evasion
Havoc: Demon → Sleep Obfuscation → Ekko/Foliage
Cobalt Strike: sleep mask / arsenal kit
```

---

## 3. 调用栈欺骗

目标：sleep 或 syscall 时 unwind 看起来像合法线程（ntdll/kernel32/user32）。

```text
SilentMoonwalk / Unwinder
Moonwalk++（栈 + 自加密研究）
ThreadStackSpoofer https://github.com/mgeeky/ThreadStackSpoofer
SysWhispers4 --stack-spoof
```

按各仓库当前 README 编译。成功标准：原被拦的 sleep/syscall 现在能持续，而不是“栈看起来好看”。

---

## 4. 和 syscall 的组合

```text
indirect/randomized syscall  → 返回地址在 ntdll gadget
+ stack spoof               → unwind 更完整
+ sleep encrypt             → 扫描窗口无明文
```

仍可能被 kernel telemetry / 行为链打到。不要宣称 0 detection。

---

## 5. 成功

```text
After: 长睡眠 payload 仍活着，原回连/命令可用
Resume: 原 Attack 模块
```
