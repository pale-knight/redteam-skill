# 离线破解

> **TECH：** 已拿到的 hash/文件 → 明文或 NT  
> **IMPACT：** 可复用口令 / NT  
> **成功：** `hashcat --show` 或 john `--show` 出明文（或 v1 还原出 NT）  
> **GATES：** 已知 `-m`、hash 完整、有字典或 mask 计划

识别与 `-m` 表 → `hash-types.md`。破解完成后回到喷洒复用或记 notes，不在这里横向。

---

## 1. hashcat 基础

```bash
hashcat -m 1000 ntlm.txt /usr/share/wordlists/rockyou.txt
hashcat -m 1000 ntlm.txt wordlist.txt -r /usr/share/hashcat/rules/best64.rule
hashcat -m 5600 netntlmv2.txt wordlist.txt -r /usr/share/hashcat/rules/best64.rule
hashcat -m 13100 tgs.hash wordlist.txt
hashcat -m 19600 tgs.hash wordlist.txt    # AES128
hashcat -m 19700 tgs.hash wordlist.txt    # AES256
hashcat -m 18200 asrep.hash wordlist.txt
hashcat -m 1800 shadow.hash wordlist.txt
hashcat -m <m> hash.txt --show
```

无 GPU：`--force`。`-O` 加快但限制密码长度，长口令不要用。

---

## 2. 规则 / mask / hybrid / PRINCE

```bash
# 规则
hashcat -m 1000 ntlm.txt custom.txt -r /usr/share/hashcat/rules/best64.rule
hashcat -m 1000 ntlm.txt custom.txt -r /usr/share/hashcat/rules/rockyou-30000.rule

# mask（已知策略：8 位、首大写、尾数字）
hashcat -m 1000 ntlm.txt -a 3 '?u?l?l?l?l?l?d?d'

# hybrid：字典 + 后缀年份
hashcat -m 1000 ntlm.txt -a 6 custom.txt '?d?d?d?d'

# PRINCE：从短词生成候选
hashcat -m 1000 ntlm.txt -a 0 <(princeprocessor < custom.txt)
```

先策略再 mask。不知道复杂度时：rockyou → best64 → 目标词 cewl。

---

## 3. john 转换

```bash
keepass2john db.kdbx > kp.hash
ssh2john id_rsa > ssh.hash
zip2john file.zip > zip.hash
rar2john file.rar > rar.hash
pdf2john file.pdf > pdf.hash
office2john file.docx > office.hash
pfx2john cert.pfx > pfx.hash

john --wordlist=rockyou.txt ssh.hash
john --rules --wordlist=rockyou.txt ssh.hash
john hash.txt --show
```

hashcat 不认的 john 格式就留在 john。PFX 常如此。

---

## 4. NetNTLMv1 → NT

无 ESS/SSP 的 NetNTLMv1 可用已知挑战还原 NT（比砸 v2 值钱）。

```bash
# 捕获见 capture-relay.md：responder --lm --disable-ess
hashcat -m 5500 netntlmv1.txt -a 3 ?a?a?a?a?a?a?a?a   # 或查当前 crack.sh / 公开 DES 还原流程
```

有 ESS 的 v1 仍要当弱挑战砸，不能当免费 NT。不确定格式时看 Responder 输出是 `NTLMv1` 还是 `NTLMv1-SSP`。

还原出的 NT 按 `-m 1000` 校验，PTH 登录校验用 nxc，横向不在这里。

---

## 5. Kerberos 材料

```bash
grep -m1 -o '\$krb5tgs\$[0-9]*\$' tgs.hash
# 23 → 13100    17 → 19600    18 → 19700
```

AES 票比 RC4 难砸。解不出来标「未破 AES TGS」，不要改成「Kerberoast 失败」。要票不在本文件。

---

## 6. 失败

```text
Wrong digest / salt  → -m 错或 hash 截断
Status: Exhausted    → 字典不够，换规则/mask，不是 hash 假
NTLMv2 几天没出     → 转通用 SMB relay 或换喷洒，不要无限 GPU
```
