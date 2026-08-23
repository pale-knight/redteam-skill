# 外部资产发现 — Domain / Organization / Origin

本文件只做资产发现和验证，不进行 Web 漏洞利用。

---

## 1. 子域名 + DNS

```bash
subfinder -d target.com -all -silent -o subs.txt
cat subs.txt | dnsx -a -aaaa -cname -resp -silent -o dns.txt
```

补主动字典时注意 wildcard：

```bash
dnsx -d target.com -w subdomains.txt -a -resp -silent
```

---

## 2. Certificate Transparency / TLS SAN

```bash
# CT 快速查询
curl -s 'https://crt.sh/?q=%25.target.com&output=json' | \
  jq -r '.[].name_value' | tr '\r' '\n' | sort -u

# 对CIDR/主机列表抓证书SAN/CN
echo 203.0.113.0/24 | tlsx -san -cn -silent -resp-only | sort -u
```

重点找：

```text
staging / dev / admin / vpn / sso / jenkins / gitlab / internal-like names
旧品牌/子公司域名
同证书覆盖但 DNS 子域枚举没出现的主机名
```

CT/TLS 结果是**资产线索**，不代表仍在线。

---

## 3. ASN / BGP / CIDR

```bash
asnmap -org 'COMPANY' -silent
asnmap -d target.com -silent
asnmap -i 203.0.113.10 -silent
```

得到 CIDR 后：

```bash
# 先范围确认，再探活
nmap -sn 203.0.113.0/24
```

企业自持 ASN 特别容易发现未挂公开域名的：

```text
VPN / mail / management / legacy / test / appliance
```

---

## 4. Internet Search Engine 聚合

`uncover` 当前可聚合 Shodan、FOFA、Censys、Quake、Hunter、ZoomEye、Netlas 等：

```bash
uncover -q 'target.com' -e shodan,fofa,censys,quake,zoomeye -f host -o search-assets.txt
uncover -q 'ssl:"target.com"' -e shodan,censys -o tls-assets.txt
```

每个引擎语法不同，复杂查询优先用各引擎原生语法。

---

## 5. Passive / Historical DNS

目标：

```text
domain → old IP
IP → old domains
first/last seen
CDN 前的 origin candidate
```

可结合 SecurityTrails / DNSDB / CIRCL / ThreatBook / PassiveDNS 服务；工具侧保留：

```bash
amass enum -passive -d target.com -o amass-passive.txt
```

历史解析只作为候选，必须重新验证当前归属和目标授权范围。

---

## 6. SPF / DMARC / MX / 邮件基础设施

```bash
dig +short TXT target.com
dig +short TXT _dmarc.target.com
dig +short MX target.com
dig +short NS target.com
```

从 SPF 递归分析：

```text
include:
redirect=
ip4:
ip6:
```

可能得到第三方 SaaS、关联域和自持 IP 段。

---

## 7. CDN / Origin Candidate

信号：CNAME/ASN/HTTP header 明确处于 CDN/WAF。

候选来源：

```text
historical A records
TLS certificate correlation
old MX/mail headers
unique body/favicon fingerprint
internet search engines
```

只做身份验证：

```bash
curl -sk --resolve target.com:443:CANDIDATE_IP https://target.com/ -D- -o /tmp/origin.body
curl -sk https://target.com/ -o /tmp/cdn.body
sha256sum /tmp/origin.body /tmp/cdn.body
```

判断：

```text
content / certificate / app fingerprint strongly matches → origin candidate high confidence
CDN error / unrelated virtual host → reject
```

---

## 8. 公有对象存储资产发现

这里只发现 endpoint/name，不做 IAM/Policy 利用：

```bash
cloud_enum -k target -k product -k target-prod
```

关注：

```text
AWS S3
Azure Blob
GCS
Alibaba OSS
S3-compatible storage
```

记录：endpoint 是否存在、匿名 HEAD/GET 的状态、名称规律。
