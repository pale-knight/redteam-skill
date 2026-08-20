# AD 管理平面攻击面

这里收纳“本身不是LDAP/Kerberos配置错误，但部署在Tier-0/CA/DC附近、可把低权限身份放大成主机高权限”的管理组件。

---

## Windows Admin Center — CVE-2026-26119

状态：**VERSION-GATED / RESEARCH-REPRODUCIBLE。**

原始研究验证了：低权限域用户在特定未修补WAC部署中，可通过认证反射取得承载WAC机器的SYSTEM上下文。

截至本次skill更新：**没有写入一个我能确认稳定公开的端到端一键PoC。** 原研究使用作者自定义的KrbRelay派生工具，因此不要虚构 `exploit.py --wac`。

### 从 /ad-recon 接收

```
Windows Admin Center存在
主机OS/版本
WAC版本
是否同时承载ADCS / DC / 高价值管理角色
相关HTTP.SYS/WAC补丁状态
```

常见发现：

```bash
nmap -Pn -sV -p 443,6516 WAC-IP
curl -kI https://WAC-IP:6516/
curl -kI https://WAC-IP/
```

### 原始攻击链

```
低权限域用户
  ↓
远程DCOM/RPC authentication coercion
  ↓
机器账户Kerberos/NTLM认证
  ↓
反射到WAC HTTP管理入口
  ↓
获得WAC session + anti-forgery token
  ↓
调用特权REST PowerShell端点
  ↓
NT AUTHORITY\SYSTEM
```

### 已知高价值REST端点

```
/api/services/WinREST/Powershell/nodes//InvokeCommand
```

研究中请求体结构类似：

```json
{"properties":{"script":"whoami.exe"}}
```

**不能直接curl复现**：正常利用需要有效的WAC认证session、cookies和anti-forgery token；每一步还涉及重新认证/反射。

### 补丁门控

```
Windows Server 2025 / Windows 11 24H2
  → HTTP.SYS原本已有更强EPA行为，旧链不应默认成立

2026-01 HTTP.SYS更新（CVE-2026-20929）
+
2026-02-17 WAC OOB更新（CVE-2026-26119）
  → 关闭原研究链
```

发现已修补：

```
→ 不进入利用
→ 只记录历史暴露/版本证据
```

### 如果在靶场中取得WAC SYSTEM

先根据WAC主机角色路由：

```
普通成员服务器
  → 本机凭据/横移

ADCS CA
  → references/adcs.md
  → CA私钥/Golden Certificate属于CA完全控制后的后续能力

DC
  → 按DC本机高权限路径处理
```

不要把“WAC存在”直接等于“域管”。
