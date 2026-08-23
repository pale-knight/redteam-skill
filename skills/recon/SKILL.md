---
name: recon
description: "通用网络与资产信息收集。面向 IP、CIDR、主机名、企业/域名等尚未明确攻击面的目标，完成资产扩展、主机发现、TCP/UDP端口发现、服务/版本/协议识别、只读服务枚举、网络设备识别和漏洞候选研判。Recon only：不执行漏洞利用、口令爆破、服务配置修改或持久化。"
---

# /recon — 通用信息收集 + 服务枚举

> **scope：** 把“只知道一个通用目标”推进到“已经知道它有哪些资产、主机、端口、服务、身份/权限状态、关系和高价值漏洞候选”。允许使用**已经掌握的凭据**做只读枚举；不做爆破、写入、配置修改、命令执行、CVE利用或持久化。
>
> `/recon` 不再承担旧版 `/recon-attack`。直连网络服务的利用统一放到独立 `/service-attack`。

工具安装问题参阅 `../shared/tools.md`。CVE 候选有精确版本才走 `../shared/cve-enrichment.md`。不要一进来把 `references/` 全读：外部拓线、端口、哪类服务枚举，分别在对应节再 Read 那一份。

---

## 开局与收尾

开局第一件事：Read `./notes.md`。没有则 `python ~/.claude/skills/bin/notes.py init`。只按已拿下/凭据继续。
走到哪条链，才 Read **一份** `references/<file>.md`。禁止开局全读、禁止凭记忆写 payload。
监听 / sudo / 输密码 / Permission denied：立刻停，说明等操作者做什么，等回报。不要假装已成功。
收尾：
1. 追加 `./notes.md`
2. `python ~/.claude/skills/bin/modules.py tail <本模块名>`
   Read 备用：`~/.claude/skills/shared/modules.yaml`
   禁止 `./modules.yaml` 和 `python ../bin/...`
3. 优先 `default_next`；`never_default` 不得当作默认（操作者点名除外）
4. 名册外的名字不许建议
5. 停。等操作者选 `/模块` 或 `/clear`
`/edr-bypass` 半条链未完：打通后回本模块，不要 /clear。


---

## 0. Recon 完成条件

Recon 不是“跑一遍 Nmap”。每个目标至少形成：

```text
Target / Asset:
IP / Hostname / CIDR / Ownership:

Open TCP:
Open UDP:

Service Map:
- port/proto → product/version → auth mode → exposure

Read-only Enumeration:
- current/anonymous identity
- security controls
- relationships / linked services
- high-value configuration state

Vulnerability Candidates:
- CPE / version confidence
- CVE
- KEV / EPSS
- public PoC?
- Nuclei template?
- prerequisites still missing?

Unresolved:
- unknown ports
- filtered/ambiguous services
- credentials required for deeper enumeration
```

**不要在 Recon 把“candidate”写成“已利用”。**

---

## 1. 目标归一化

```bash
# IP / hostname basic
getent hosts TARGET
host TARGET
whois TARGET 2>/dev/null | head -80

# IP ownership
whois 203.0.113.10 | grep -Ei 'origin|route|netname|org|country' | head -40
```

记录：

```text
Input = IP / hostname / CIDR / organization / domain
Resolved IPs = ...
ASN / owner = ...
Known scope boundaries = ...
```

如果一个 hostname 同时解析多个 IP，不要只扫第一条；记录所有 A/AAAA。

---

## 2. 外部资产扩展

企业/域名级任务按 `references/external-recon.md` 做：

```text
Subdomain / DNS
Passive DNS / historical DNS
CT / TLS SAN-CN
ASN / BGP / CIDR
Internet search engines
SPF / DMARC / MX
CDN / origin candidates
Cloud object-storage asset names
```

中国企业/SRC场景的 ICP、APP、小程序、股权主体等放在 `references/enterprise-osint.md`，主流程不默认加载。

---

## 3. 主机与端口发现

优先将“快速发现”和“准确识别”拆开：

```bash
# 大量目标快速 TCP
naabu -l hosts.txt -tp full -verify -o tcp-open.txt

# 单目标/少量目标精扫
nmap -Pn -sV --version-all -p- TARGET -oA tcp-full

# UDP 不要只扫 20 个端口；先常用，再按证据扩展
sudo nmap -Pn -sU -sV --top-ports 100 TARGET -oA udp-top100
```

局域网存活发现：

```bash
nmap -sn 10.10.10.0/24 -oA alive
sudo arp-scan --localnet
```

完整策略 → `references/network-discovery.md`。

---

## 4. 服务识别与未知端口

对每个开放端口先做**协议确认**，不要只靠端口号猜服务：

```bash
nmap -Pn -sV --version-all -p PORT TARGET
nc -nv TARGET PORT
```

TLS候选：

```bash
echo TARGET:PORT | tlsx -san -cn -silent
openssl s_client -connect TARGET:PORT -servername HOST </dev/null 2>/dev/null | \
  openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

HTTP候选：

```bash
echo TARGET:PORT | httpx -sc -title -server -tech-detect -silent
```

输出至少包含：

```text
protocol confidence
product/version confidence
TLS certificate names
HTTP/non-HTTP
banner / ALPN / auth scheme
```

---

## 5. 服务级只读枚举

按发现的**那一类**服务只 Read 一份，不要把整套速查执行：

```text
SMB/FTP/SMTP/DNS/NFS/SSH/RDP/WinRM/SNMP → references/service-enum.md
库/NoSQL                                 → references/database-enum.md
Docker/Vault/Consul/Nomad/etcd           → references/infrastructure-enum.md
队列                                     → references/messaging-enum.md
打印机/NAS/BMC/网设                      → references/network-devices-enum.md
NSE 需要时                               → references/nse-scripts.md
```

### Recon 允许

```text
version / banner / feature discovery
anonymous access check
known credential read-only enumeration
identity / role / privilege readout
share/index/topic/job/container listing
read-only relationship mapping
configuration GET / SHOW / INFO
```

### Recon 不允许

```text
password spraying / brute force
CREATE / ALTER / SET / CONFIG SET
upload / overwrite / delete
enable xp_cmdshell / external scripts
submit job / run container
write SSH key / cron / webshell
CVE exploitation / exploit NSE
```

---

## 6. 漏洞候选研判

先建立高置信版本/CPE，再关联漏洞：

```bash
# 现代候选引擎：可看 KEV / EPSS / PoC / template
vulnx search "PRODUCT && severity:critical" --limit 20
vulnx search "PRODUCT && is_kev:true" --limit 20

# cvemap（需要PDCP认证，适合CPE/厂商过滤）
cvemap -p PRODUCT -s critical,high -f age,kev,epss,poc,template
```

具体 → `../shared/cve-enrichment.md` 与 `references/vulnerability-candidates.md`。

**优先级不是 CVSS 单指标：**

```text
exact version/CPE match
+ reachable network path
+ prerequisite satisfied
+ KEV / high EPSS
+ public PoC / reliable template
```

---

## 7. 内网 Recon

已在目标主机上但尚未建立完整代理时，使用 `references/internal-enum.md`：

```text
interface / route / ARP-neighbor / DNS
local connections
known internal hosts
high-value service families
```

原则：本机上下文优先，盲扫整个 RFC1918 空间最后考虑。

---

## 8. 输出格式

```text
[HOST] 10.10.10.25

22/tcp OpenSSH ...
  Auth: publickey,password
  Version confidence: high
  Candidate CVEs: ...

1433/tcp Microsoft SQL Server ...
  Identity: CORP\\sqluser
  sysadmin: false
  IMPERSONATE: loginX
  Linked Server: SQL02
  xp_cmdshell: disabled

161/udp SNMP
  readable community/token: <known>
  sysDescr: HP LaserJet ...
  Related ports: 631/9100

Unresolved:
- 9001/tcp protocol ambiguous; TLS=no, HTTP=no, banner=...
```

Recon 到此完成。把上表写入 `./notes.md`。候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。
