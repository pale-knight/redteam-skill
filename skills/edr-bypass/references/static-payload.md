# Static / On-write Evasion

阻断发生在 **文件落地或 image load 之前**。

---

## 1. 确认

```text
exe/dll 一写就被隔离
rundll32 加载失败
MOTW / SmartScreen 拦下载
```

脚本被拦 → `script-runtime.md`。进程起来后才死 → `memory-execution.md`。

---

## 2. 分离加载

不要把最终 payload 以明文 PE 落地。

```bash
# Donut: PE/.NET → 位置无关 shellcode
git clone https://github.com/TheWover/donut.git

# ScareCrow / Freeze：生成带签名伪装或 syscall stub 的 loader
# github.com/optiv/ScareCrow
# github.com/Optiv/Freeze
```

流程：

```text
最终 exe → Donut shellcode
→ loader（加密 + 运行时解密 + 非 CRT 注入）
→ loader 用允许的宿主执行（见 application-control.md）
```

---

## 3. MOTW

从浏览器/邮件下来的文件带 Zone.Identifier。

```powershell
Get-Item payload.exe -Stream Zone.Identifier -ErrorAction SilentlyContinue
Unblock-File .\payload.exe   # 仅当文件已在手且策略允许；钓鱼链应避免依赖这个
```

钓鱼侧优先 **不落地**（ClickFix 剪贴板执行）或 **无 MOTW 的执行路径**（Explorer 地址栏 FileFix）。那属于 `/phishing`，本模块只在 payload 已被拦时改 loader。

---

## 4. 签名 / 侧载

合法签名程序 + 可写目录 DLL 侧载。需要：

```text
目标机已有或你能投放该签名 EXE
DLL 搜索顺序可控
侧载 DLL 导出被 EXE 调用
```

没有具体 EXE/DLL 组合就不要编侧载命令。

---

## 5. 成功

```text
After: loader 能在目标落地并进入执行（或内存执行不再被静态拦）
仍被拦: 可能已经进入行为层，转 process/memory
Resume: 原 Attack 模块
```
