# Parser Differential / Unicode Normalization 详细参考

> 核心思想：一个输入会经过多个 parser。漏洞来自 **A 组件和 B 组件对同一字节序列理解不同**，不是“某个神奇分隔符通杀”。

---

## 1. 先画 Parser Chain

```
Browser/Client
  ↓
CDN/WAF
  ↓
Reverse Proxy
  ↓
Framework body parser/router
  ↓
Auth middleware
  ↓
Business logic
  ↓
ORM/DB / downstream API
```

问：

```
每层如何解析 path/query/header/body？
是否 decode/normalize？做几次？
重复字段取 first / last / concat / reject？
```

如果 `/web-recon` 的 Backslash Powered Scanner 已经给出 server-side differential/evidence：

```text
先在 Repeater 复现原始差异
→ 一次只改变一个字符/编码/重复字段
→ 找到最小触发条件
→ 再判断属于 JSON/HPP/path/escape/injection 哪一类
```

不要直接复用扫描器的大 payload 作为最终利用。

---

## 2. Duplicate JSON Keys

不同 JSON parser 对重复 key 可能：

```
first wins
last wins
reject
保留全部
```

靶场测试：

```json
{"role":"user","role":"admin"}
```

或：

```json
{"amount":1,"amount":9999}
```

如果 WAF/auth 读 first，应用读 last，就可能造成 auth/business logic bypass。

必须对照一个正常请求；仅服务器接受重复 key 不等于漏洞。

---

## 3. Duplicate Headers

高价值：

```http
Authorization: Bearer LOW_TOKEN
Authorization: Bearer HIGH_OR_INVALID
```

```http
Host: public.example
Host: internal.example
```

```http
Content-Length: 10
Content-Length: 100
```

不同层可能 first/last/merge。`Content-Length` 差异进一步属于 HTTP Desync → `http-desync.md`。

---

## 4. Content-Type Differential

同 endpoint 分别：

```
application/x-www-form-urlencoded
application/json
multipart/form-data
application/xml
text/plain
```

例：

```
正常form被WAF拦截
→ JSON body是否仍被后端绑定到同一参数？
```

不要把“换 Content-Type 成功”直接说 WAF bypass，先确认后端业务语义相同。

---

## 5. Multipart Differential

重点：

```
boundary quoting
LF vs CRLF
重复 Content-Disposition
重复 name/filename
filename*= UTF-8
空filename
header折叠/额外CR
```

典型差异：WAF 检查第一个 filename，框架使用第二个。

靶场可以在 Burp 中构造：

```http
Content-Disposition: form-data; name="file"; filename="safe.txt"
Content-Disposition: form-data; name="file"; filename="shell.php"
```

若前后组件解释不同，再结合文件上传链。

---

## 6. URL Parser Differential

测试：

```
//host/path
\\host\path
http://user@host/
http://host#@allowed/
http://host?@allowed/
http://127.1/
http://2130706433/
```

对 SSRF/open redirect/auth allowlist 特别重要。

若涉及 SSRF → `ssrf.md`。

---

## 7. Path Delimiter / Normalization

```
/admin
/admin/
/admin;foo
/admin%3Bfoo
/admin%2Ffoo
/admin/./
/admin/%2e/
/admin/%2e%2e/public
/admin%3F.css
/admin%23.css
```

比较：

```
proxy ACL
framework route
cache key
```

可能升级为：

```
ACL bypass
cache deception
WAF bypass
route confusion
```

---

## 8. Unicode Normalization

### 核心

```
组件A过滤原始Unicode
组件B做 NFKC/NFKD/Best-Fit/IDNA 后变成危险ASCII或不同标识符
```

先在本地生成候选：

```
python3 - <<'PY'
import unicodedata
samples=['＜script＞','ＳＥＬＥＣＴ','＇','／','：']
for s in samples:
    print(repr(s), 'NFKC=>', repr(unicodedata.normalize('NFKC',s)))
PY
```

这只是候选生成；目标是否 normalize 必须通过响应差异确认。

### 适用面

```
WAF keyword bypass
path/auth bypass
username/account confusion
hostname/domain allowlist
email/domain validation
```

不要只靠视觉同形字；真正有用的是**后续组件会把它规范化为另一语义**。

---

## 9. Email Parser Differential

Web 应用中高价值：

```
企业域名注册限制
邀请系统
password reset
SSO/email binding
```

应用 parser 和邮件库对：

```
quoted local-part
comments
encoded-word
Unicode
multiple @ / display-name
```

可能不同。

如果能把“外部邮箱”在 auth 层解析成 `@corp.com`，但邮件实际投递到攻击者 → 可形成 account takeover。

---

## 10. 从 Differential 到 Shell

```
parser differential
  ↓
auth/WAF/path/cache bypass
  ↓
高权限功能或注入入口
  ↓
上传 / SSTI / command injection / admin plugin
  ↓
Shell
```

差异本身只是 primitive；必须记录到底哪两层语义不同。
