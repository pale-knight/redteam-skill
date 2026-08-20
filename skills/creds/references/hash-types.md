# Hashcat -m 类型对照

识别：

```bash
hashid '<hash>'
hashcat --example-hashes | grep -i ntlm
```

不确定就先 `hashid`，不要猜 `-m`。Kerberoast 必须看 etype，不要默认 13100。

---

## 渗透高频

| Hash | -m | 来源 |
|---|---|---|
| NTLM | 1000 | SAM / secretsdump / pypykatz |
| LM | 3000 | 老 SAM |
| NetNTLMv1 / v1+ESS | 5500 | Responder `--lm`；无 ESS 时常可还原 NT |
| NetNTLMv2 | 5600 | Responder 默认 |
| AS-REP (etype 23) | 18200 | GetNPUsers / Rubeus |
| Kerberoast TGS RC4 etype 23 | 13100 | GetUserSPNs；`$krb5tgs$23$` |
| Kerberoast AES128 etype 17 | 19600 | `$krb5tgs$17$` |
| Kerberoast AES256 etype 18 | 19700 | `$krb5tgs$18$` |
| Kerberos AS-REQ etype 23 | 7500 | 少见 |
| mscachev2 (DCC2) | 2100 | secretsdump 域缓存 |
| sha512crypt `$6$` | 1800 | Linux shadow |
| sha256crypt `$5$` | 7400 | Linux shadow |
| md5crypt `$1$` | 500 | 老 shadow |
| bcrypt | 3200 | Web / 现代应用 |

抓到 `$krb5tgs$` 先看数字：

```bash
grep -o '\$krb5tgs\$[0-9]*\$' tgs.hash
```

票如果是 **当前 `/ad-attack` Kerberoast/AS-REP 链** 刚要来的：砸+用都在 `/ad-attack`。本文件给 AD 当查表，也给「操作者把已有 hash 当独立凭据作业」用。

---

## Web / 应用

| Hash | -m | 来源 |
|---|---|---|
| MD5 | 0 | 弱应用 |
| SHA1 | 100 | |
| SHA256 | 1400 | |
| SHA512 | 1700 | |
| WordPress / phpass | 400 | wp_users |
| Joomla | 11 | |
| Drupal 7 | 7900 | |
| Django PBKDF2-SHA256 | 10000 | |
| JWT HS256 | 16500 | 三段 token 的密钥爆破 |
| JWT HS384 / HS512 | 16501 / 16511 | 以 hashcat 当前 `--help` 为准 |

---

## 文件 / 密钥

| 对象 | -m 或转换 | 工具 |
|---|---|---|
| KeePass | 13400 | `keepass2john db.kdbx` |
| SSH 私钥 | 22921（版本随 hashcat 变） | `ssh2john id_rsa` |
| ZIP PKZIP | 17200 | `zip2john` |
| ZIP WinZip AES | 13600 | `zip2john` |
| RAR3 / RAR5 | 12500 / 13000 | `rar2john` |
| 7z | 11600 | `7z2john` |
| PDF | 10400–10700 | `pdf2john` |
| Office 2013+ | 9600 | `office2john` |
| PFX/PKCS#12 | john 格式 | `pfx2john cert.pfx` |
| WPA/WPA2 | 22000 | hcxpcapngtool |

转换后仍用 john/hashcat 解。解出的口令回到喷洒/复用，不要在这里 SSH 登录打内网。

---

## 实用

```bash
hashcat -m 1000 ntlm.txt /usr/share/wordlists/rockyou.txt
hashcat -m 1000 ntlm.txt wordlist.txt -r /usr/share/hashcat/rules/best64.rule
hashcat -m 1000 ntlm.txt --show
hashcat -m 1000 ntlm.txt wordlist.txt --force   # 无 GPU

# john
keepass2john db.kdbx > kp.hash
ssh2john id_rsa > ssh.hash
pfx2john cert.pfx > pfx.hash
john --wordlist=rockyou.txt ssh.hash
john ssh.hash --show
```

NetNTLMv1 无 ESS 的还原、mask/hybrid/PRINCE → `offline-crack.md`。
