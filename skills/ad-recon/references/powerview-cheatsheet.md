# PowerView 常用命令速查

PowerView.ps1: `/usr/share/windows-resources/powersploit/Recon/PowerView.ps1`
PowerView.py（Kali远程）: `powerview corp.com/user:'pass'@DC-IP`

---

## 域信息

```
Get-NetDomain                                    # 域基本信息(名称/DC/森林)
Get-NetDomainController                          # 域控列表
Get-DomainPolicy                                 # 域策略(密码策略等)
```

## 用户

```
Get-NetUser                                      # 全部用户
Get-NetUser | select cn,pwdlastset,lastlogon     # 精简输出
Get-NetUser -SPN | select samaccountname,serviceprincipalname  # SPN账户
Get-NetUser -AdminCount | select samaccountname  # 特权用户
Get-NetUser jen                                  # 单个用户详情
```

## 组

```
Get-NetGroup | select cn                         # 全部组
Get-NetGroup "Domain Admins" | select member      # DA成员
Get-NetGroup "Enterprise Admins" | select member
Get-NetGroupMember "Domain Admins" -Recurse      # 递归展开嵌套组
```

## 计算机

```
Get-NetComputer                                  # 全部计算机
Get-NetComputer | select operatingsystem,dnshostname
Get-NetComputer -Unconstrained | select name     # 非约束委派
```

## 权限/ACL

```
Get-ObjectAcl -Identity "jen"                    # 用户ACL
Get-ObjectAcl -Identity "Domain Admins"          # 组ACL
Get-ObjectAcl -Identity "jen" | ? {$_.ActiveDirectoryRights -eq "GenericAll"}

# 过滤特定权限
Get-ObjectAcl -Identity "Management Department" | ? {$_.ActiveDirectoryRights -match "GenericAll|WriteDACL|WriteOwner|ForceChangePassword"} | select SecurityIdentifier,ActiveDirectoryRights

Convert-SidToName S-1-5-21-...-1104              # SID转名称
```

## SPN

```
Get-NetUser -SPN                                 # Kerberoast目标
setspn -L iis_service                            # 查看特定用户SPN
```

## 共享

```
Find-DomainShare                                 # 域共享发现
Find-DomainShare -CheckShareAccess               # 只列可访问的
```

## 会话/登录

```
Find-LocalAdminAccess                            # 我在哪有管理权限
Get-NetSession -ComputerName files04             # 谁登录了files04
```

## 委派

```
Get-DomainComputer -Unconstrained                # 非约束委派
Get-DomainUser -TrustedToAuth                    # 约束委派(用户)
Get-DomainComputer -TrustedToAuth                # 约束委派(计算机)
```

## GPO

```
Get-NetGPO                                       # 全部GPO
Get-NetGPO | select displayname,whenchanged
```

## 信任

```
Get-NetDomainTrust                               # 域信任关系
Get-NetForestDomain                              # 林中所有域
```

---

## PowerView.ps1 → PowerView.py 命令映射

| PowerView.ps1 | PowerView.py |
|---|---|
| Get-NetDomain | Get-Domain |
| Get-NetUser | Get-DomainUser |
| Get-NetGroup | Get-DomainGroup |
| Get-NetComputer | Get-DomainComputer |
| Get-ObjectAcl | Get-DomainObjectAcl -ResolveGUIDs |
| Convert-SidToName | ConvertFrom-SID |
| Find-DomainShare | Find-DomainShare |
