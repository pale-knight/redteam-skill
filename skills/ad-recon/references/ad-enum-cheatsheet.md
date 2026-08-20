# 域枚举按任务速查

每个任务给多工具选项，优先使用从Kali远程执行的工具。

---

## 用户枚举

```
# nxc（首选）
nxc smb DC-IP -u jen -p 'pass' --users
nxc ldap DC-IP -u jen -p 'pass' --users

# BloodyAD
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get children --otype user

# ldapsearch
ldapsearch -x -H ldap://DC-IP -D 'jen@corp.com' -w 'pass' -b 'dc=corp,dc=com' '(objectClass=user)' sAMAccountName description memberOf

# ldapdomaindump（全量dump为HTML/JSON）
ldapdomaindump -u 'corp.com\jen' -p 'pass' DC-IP -o ./ldap-dump/

# impacket
impacket-GetADUsers -all corp.com/jen:'pass' -dc-ip DC-IP
```

---

## 组枚举

```
# nxc
nxc smb DC-IP -u jen -p 'pass' --groups
nxc ldap DC-IP -u jen -p 'pass' --groups

# BloodyAD
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get children 'CN=Domain Admins,CN=Users,DC=corp,DC=com'

# ldapsearch
ldapsearch ... '(objectClass=group)' cn member
ldapsearch ... '(memberOf=CN=Domain Admins,CN=Users,DC=corp,DC=com)' sAMAccountName
```

---

## 计算机枚举

```
# nxc（快速扫网段）
nxc smb SUBNET/24 -u jen -p 'pass'

# BloodyAD
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get children --otype computer

# ldapsearch
ldapsearch ... '(objectClass=computer)' cn operatingSystem dNSHostName
```

---

## SPN 账户（Kerberoast目标）

```
# impacket（首选，直接导出TGS hash）
impacket-GetUserSPNs corp.com/jen:'pass' -dc-ip DC-IP -request

# ldapsearch
ldapsearch ... '(&(objectClass=user)(servicePrincipalName=*))' sAMAccountName servicePrincipalName

# nxc
nxc ldap DC-IP -u jen -p 'pass' --kerberoasting output.txt
```

---

## ACL/可写对象

```
# BloodyAD（首选，最直观）
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get writable --right ALL
bloodyAD ... get writable --right WRITE --otype user
bloodyAD ... get writable --right WRITE --otype group
bloodyAD ... get writable --right WRITE --otype computer

# 查特定对象ACL
bloodyAD ... get object 'Domain Admins' --attr nTSecurityDescriptor

# impacket dacledit（查+改ACL）
impacket-dacledit -action read -target 'Domain Admins' corp.com/jen:'pass'
```

---

## 共享

```
# nxc（首选，批量快扫）
nxc smb SUBNET/24 -u jen -p 'pass' --shares

# smbclient
smbclient -L //DC-IP/ -U 'jen%pass'

# 敏感文件搜索
nxc smb SUBNET/24 -u jen -p 'pass' -M spider_plus
```

---

## 会话/登录

```
# nxc
nxc smb SUBNET/24 -u jen -p 'pass' --sessions
nxc smb SUBNET/24 -u jen -p 'pass' --loggedon-users
```

---

## 委派

```
# impacket（首选，一次列全）
impacket-findDelegation corp.com/jen:'pass'

# BloodyAD
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get object 'TARGET$' --attr msDS-AllowedToDelegateTo,userAccountControl

# ldapsearch
ldapsearch ... '(&(objectClass=computer)(userAccountControl:1.2.840.113556.1.4.803:=524288))' cn  # 非约束
ldapsearch ... '(msDS-AllowedToDelegateTo=*)' cn msDS-AllowedToDelegateTo  # 约束
```

---

## GPP 密码

```
# nxc（首选，自动搜）
nxc smb DC-IP -u jen -p 'pass' -M gpp_autologin
nxc smb DC-IP -u jen -p 'pass' -M gpp_password

# 手动
gpp-decrypt "<cpassword值>"
```

---

## 密码策略

```
# nxc
nxc smb DC-IP -u jen -p 'pass' --pass-pol

# ldapsearch
ldapsearch ... '(objectClass=domain)' lockoutThreshold lockoutDuration pwdHistoryLength minPwdLength
```

---

## GPO

```
# BloodyAD
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get children --otype gpo

# ldapsearch
ldapsearch ... '(objectClass=groupPolicyContainer)' displayName gPCFileSysPath
```

---

## 域信任

```
# BloodyAD
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get children --otype trust

# ldapsearch
ldapsearch ... '(objectClass=trustedDomain)' cn trustDirection trustType

# nltest（域内Windows）
nltest /domain_trusts
```

---

## ADCS 证书服务

```
# certipy（最全面）
certipy find -u jen@corp.com -p 'pass' -dc-ip DC-IP -vulnerable

# nxc
nxc ldap DC-IP -u jen -p 'pass' -M adcs
```

---

## DNS

```
# BloodyAD
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get dnsDump

# adidnsdump
adidnsdump -u 'corp.com\jen' -p 'pass' DC-IP
```

---

## LAPS / Windows LAPS

不要只查 legacy `ms-Mcs-AdmPwd`。

```bash
# 快速
nxc ldap DC-IP -u jen -p 'pass' -M laps

# legacy
ldapsearch ... '(ms-Mcs-AdmPwd=*)' cn ms-Mcs-AdmPwd ms-Mcs-AdmPwdExpirationTime

# Windows LAPS
ldapsearch ... '(objectClass=computer)' cn \
  msLAPS-Password msLAPS-EncryptedPassword \
  msLAPS-PasswordExpirationTime msLAPS-CurrentPasswordVersion
```

Windows 管理主机：

```powershell
Get-LapsADPassword -Identity WS01 -AsPlainText
Find-LapsADExtendedRights -Identity 'OU=Workstations,DC=corp,DC=com'
```

完整 schema、EncryptedPassword/history、DSRM、Server 2025 `msLAPS-CurrentPasswordVersion` → **windows-laps.md**。

---

## 附录：PowerView.ps1（⚠️ 仅无EDR环境备选）

现代EDR会检测并阻止PowerView.ps1加载。仅在确认无EDR/Defender时使用。

```
powershell -ep bypass
Import-Module .\PowerView.ps1

Get-NetDomain                          # 域信息
Get-NetUser | select cn,pwdlastset     # 用户
Get-NetGroup "Domain Admins" | select member  # DA成员
Get-NetComputer                        # 计算机
Get-ObjectAcl -Identity "target"       # ACL
Find-LocalAdminAccess                  # 本地管理员访问
Find-DomainShare                       # 共享
Get-DomainComputer -Unconstrained      # 非约束委派
Get-NetDomainTrust                     # 信任关系
```

---

## 现代DC版本 / Kerberos加密姿态

```
# DC OS
ldapsearch -x -H ldap://DC-IP -D 'jen@corp.com' -w 'pass' \
  -b 'dc=corp,dc=com' \
  '(&(objectClass=computer)(userAccountControl:1.2.840.113556.1.4.803:=8192))' \
  dNSHostName operatingSystem operatingSystemVersion

# Kerberoast目标同时记录etype能力
ldapsearch -x -H ldap://DC-IP -D 'jen@corp.com' -w 'pass' \
  -b 'dc=corp,dc=com' \
  '(&(objectClass=user)(servicePrincipalName=*))' \
  sAMAccountName servicePrincipalName msDS-SupportedEncryptionTypes pwdLastSet
```

```
0x04 = RC4
0x08 = AES128
0x10 = AES256
```

---

## dMSA / BadSuccessor候选

```
# 已有dMSA
ldapsearch -x -H ldap://DC-IP -D 'jen@corp.com' -w 'pass' \
  -b 'dc=corp,dc=com' \
  '(objectClass=msDS-DelegatedManagedServiceAccount)' \
  sAMAccountName distinguishedName dNSHostName \
  msDS-DelegatedMSAState msDS-ManagedAccountPrecededByLink msDS-GroupMSAMembership

# NetExec候选OU
nxc ldap DC-IP -u jen -p 'pass' -M badsuccessor
```

输出只做候选判断；利用 → `/ad-attack references/dmsa.md`。

---

## Identity Confusion候选

```
# 可写用户/计算机
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get writable --right WRITE --otype user
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get writable --right WRITE --otype computer

# 全部可写对象中额外检查OU/Container
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get writable --right ALL
```

如果可以写受控对象的 `userPrincipalName`，且DC未修补2026年4月更新 → ResetNightmare候选。

如果可以写 `servicePrincipalName`，且DC未修补2026年3月更新 → KerberLoss研究候选。

---

## Ghost SPN

域内Windows：

```powershell
. .\TestComputerSpnDNS.ps1
Test-ComputerSpnDns
```

手工复核：

```
SPN指向hostname
+
hostname没有DNS记录
= Ghost SPN候选
```

recon阶段不创建DNS记录。

---

## Windows Admin Center

```
nmap -Pn -sV -p 443,6516 TARGETS
curl -kI https://TARGET:6516/
curl -kI https://TARGET/
```

记录WAC版本、主机OS、是否同时承载CA/DC，以及补丁状态。
