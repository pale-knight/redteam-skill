# 网络发现 / 端口扫描 / 未知协议识别

---

## 1. TCP 发现

大量目标：

```bash
naabu -l hosts.txt -tp 1000 -verify -o tcp-top1000.txt
naabu -l priority-hosts.txt -tp full -verify -o tcp-full.txt
```

`naabu` 适合快速端口发现；服务确认交给 Nmap：

```bash
cut -d: -f1 tcp-full.txt | sort -u > ips.txt
nmap -Pn -sV --version-all -iL ips.txt -p 22,80,443,445,1433,3306,5432,6379,8080,8443
```

单目标：

```bash
nmap -Pn -sV --version-all -p- TARGET -oA tcp-full
```

---

## 2. UDP

不要把 UDP 当“顺便 top20”：

```bash
sudo nmap -Pn -sU -sV --top-ports 100 TARGET -oA udp-top100
```

根据上下文定向补：

```bash
sudo nmap -Pn -sU -sV -p 53,67,68,69,123,137,161,500,514,520,623,1900,4500,5353 TARGET
```

高价值：

```text
DNS 53
SNMP 161
IPMI 623
IKE 500/4500
TFTP 69
NTP 123
mDNS/SSDP 5353/1900
```

---

## 3. Host Discovery

同网段优先 ARP：

```bash
sudo arp-scan --localnet
nmap -sn 10.10.10.0/24
```

被 ICMP 过滤时，不要把 `ping` 失败当成主机离线：

```bash
nmap -Pn -p 22,80,443,445 TARGET
```

---

## 4. Unknown Port

顺序：

```text
Nmap version detection
→ raw banner
→ TLS?
→ HTTP?
→ protocol-specific probe
→ product/version candidate
```

```bash
nmap -Pn -sV --version-all -p PORT TARGET
nc -nv TARGET PORT

echo TARGET:PORT | httpx -sc -title -server -silent
echo TARGET:PORT | tlsx -san -cn -silent
```

TLS手工：

```bash
openssl s_client -connect TARGET:PORT -servername HOST -alpn 'h2,http/1.1' </dev/null
```

---

## 5. IPv6

发现 AAAA 或本地 IPv6 时不要忽略：

```bash
subfinder -d target.com -silent | dnsx -aaaa -resp -silent
nmap -6 -Pn -sV -p- IPV6
```

局域网邻居：

```bash
ip -6 neigh
```

---

## 6. 输出去重

建议统一：

```text
host,ip,port,transport,service,product,version,tls,http,title,confidence
```

不要把多个工具的猜测直接合并成“事实”；冲突时保留证据。
