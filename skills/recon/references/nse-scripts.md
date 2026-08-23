# Nmap NSE — Recon 安全选择

NSE 没有 sandbox。第三方脚本和类别扫描都要先看 help/category。

---

## 1. 类别原则

```text
safe       → 设计上不主动利用/耗尽资源，但仍不是绝对零风险
discovery  → 信息发现
version    → 随 -sV 自动选择
intrusive  → 可能造成资源压力/被视为攻击
exploit    → 主动利用
dos        → 可能导致拒绝服务
brute      → 凭据爆破
vuln       → 检查已知漏洞；并不保证 safe
```

Recon 默认选择具体 `safe/discovery` 脚本，不使用广义 `vuln` 类别。

---

## 2. 先看脚本属性

```bash
nmap --script-help smb2-security-mode
nmap --script-help redis-info
nmap --script-help SCRIPT
```

只选 `safe/discovery/version` 且适合当前服务的脚本。

---

## 3. 推荐枚举

```bash
# SMB
nmap -p445 --script smb-protocols,smb2-security-mode,smb2-time,smb-os-discovery TARGET

# SSH
nmap -p22 --script ssh-hostkey,ssh-auth-methods,ssh2-enum-algos TARGET

# FTP
nmap -p21 --script ftp-syst,ftp-anon TARGET

# DNS
nmap -sU -p53 --script dns-recursion TARGET

# NFS/RPC
nmap -p111,2049 --script rpcinfo,nfs-showmount,nfs-statfs TARGET

# MSSQL
nmap -p1433 --script ms-sql-info,ms-sql-ntlm-info TARGET

# Redis
nmap -p6379 --script redis-info TARGET

# Mongo
nmap -p27017 --script mongodb-info TARGET

# IPMI
nmap -sU -p623 --script ipmi-version TARGET

# RDP
nmap -p3389 --script rdp-enum-encryption,rdp-ntlm-info TARGET
```

---

## 4. 不在 Recon 默认使用

```text
*-brute
http-put
ms-sql-xp-cmdshell
jdwp-exec
shellshock exploit scripts
DoS/fuzzer categories
broad --script vuln
```
