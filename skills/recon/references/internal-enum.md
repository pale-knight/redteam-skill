# 内网快速 Recon（立足点侧）

目标：先利用本机已有信息建立内部资产图，再决定是否从攻击机完整扫描。

---

## Linux

```bash
ip -br addr
ip route
ip neigh
cat /etc/resolv.conf
cat /etc/hosts
ss -tunap 2>/dev/null | head -100
getent hosts $(hostname -f) 2>/dev/null
```

本机配置线索：

```bash
env | grep -Ei 'proxy|http_proxy|https_proxy|no_proxy'
grep -RniE 'https?://|jdbc:|redis://|mongodb://|amqp://|kafka|vault|consul|nomad' /etc 2>/dev/null | head -100
```

低噪声邻居优先 `ip neigh` / ARP / DNS；必要时才主动探测。

---

## Windows

```powershell
ipconfig /all
route print
arp -a
Get-NetTCPConnection | Sort-Object RemoteAddress | Select-Object -First 100
Get-DnsClientServerAddress
Get-Content C:\Windows\System32\drivers\etc\hosts
```

环境/代理：

```powershell
Get-ChildItem Env: | ? Name -match 'proxy'
netsh winhttp show proxy
```

---

## 小范围主动探测

已经从 route/ARP/DNS 得到明确子网后：

```bash
nmap -sn 10.20.30.0/24
nmap -Pn -sT -p 22,53,80,443,445,1433,3306,5432,5672,6379,8200,8500,9092,9100 10.20.30.0/24 --open
```

如果当前立足点不能安装扫描器，可用原生命令做少量目标验证，而不是并发扫整个企业网。

---

## 服务家族标记

```text
Windows/AD clues
Database
CI/CD/build
Kubernetes/container
Message queue
Vault/Consul/Nomad
Printer/BMC/network appliance
Storage/NAS
```

只记录发现，不在本文件执行对应利用。
