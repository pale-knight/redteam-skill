# HTTP Desync / Request Smuggling 详细参考

> 适用：已经从 `/web-recon` 看到 CDN/WAF/reverse proxy → backend 的多组件 HTTP 边界。该类漏洞误报很常见，**必须证明不同组件对请求边界解释不同**。单纯 HTTP pipelining、客户端复用连接、两个正常响应连在一起都不是漏洞。

---

## 1. 前置条件

优先级高：

```
HTTP/2 frontend → HTTP/1.1 backend
CDN/WAF → Nginx/Apache/IIS/app server
不同Server header/error page交替出现
Connection keep-alive
Transfer-Encoding / Content-Length 行为不一致
```

低优先级：单一应用服务器、连接始终关闭、明确 end-to-end H2 且无转换。

---

## 2. 工具优先

### Burp HTTP Request Smuggler

优先使用官方/成熟 Burp 扩展做探测，再人工确认。

不要仅依据 scanner 的“possible”标记直接报漏洞。

### smuggler.py

```
python3 smuggler.py -u https://TARGET
```

用于经典 TE/CL 差异候选；现代 H2/0.CL/CRLF 类仍建议 Burp 工具和手工验证。

---

## 3. 经典请求边界

### CL.TE

前端按 Content-Length，后端按 Transfer-Encoding。

概念请求：

```http
POST / HTTP/1.1
Host: TARGET
Content-Length: 6
Transfer-Encoding: chunked

0

X
```

检测时用**无害 timeout/404 probe**，不要一开始污染其他用户队列。

### TE.CL

前端 TE，后端 CL。

### TE.TE

两边都识别 TE，但其中一端对混淆 `Transfer-Encoding` 语法处理不同：

```
Transfer-Encoding: chunked
Transfer-Encoding : chunked
Transfer-Encoding: xchunked
Transfer-Encoding: chunked, identity
```

具体有效语法强依赖产品版本。

---

## 4. Modern Desync Matrix

```
CL.TE
TE.CL
TE.TE
CL.0
0.CL
H2.CL
H2.TE
H2C downgrade
Client-side desync
Request tunnelling
Chunk extension / line-terminator differential
CRLF-powered desync
```

### CL.0

后端忽略 request body/Content-Length，body 残留成为下一请求前缀。

### 0.CL

前端认为无 body，后端按 Content-Length 等待/消费数据。

### H2.CL / H2.TE

HTTP/2 本身没有传统 TE chunked framing，但前端降级到 H1 时可能错误复制 `Content-Length`/TE 语义。

使用 Burp Repeater 的 HTTP/2 inspector/Request Smuggler，不要靠 curl 伪造非法 H2 header。

---

## 5. 如何避免“HTTP Pipelining = 漏洞”的误报

**错误判断：**

```
同一TCP连接发送两个正常请求
→ 收到两个正常响应
→ 误判RQP
```

真正需要：

```
同一攻击请求
前端认为边界在A
后端认为边界在B
    ↓
残留字节影响后续独立请求/响应
```

验证方式：

1. 用 Burp 的单连接控制，不让客户端自己做 pipelining。
2. 发送 harmless prefix，观察**另一个独立请求**是否被改变。
3. 重复多次确认，不把网络抖动/代理重试当结果。

---

## 6. 2025：HTTP/1.1 Desync Endgame

现代研究重点已经不只是 CL.TE/TE.CL，尤其关注：

```
0.CL / double-desync
chunk parser line terminator
upstream HTTP/1.1 downgrade
```

如果前端对客户端提供 H2，但 upstream 仍是 H1，优先级提高。

---

## 7. 2026：CRLF-Powered Desync

2026-08 新研究展示：某些服务器/代理允许 path/header 解析中的 CRLF 注入进一步“斩断”HTTP stream，从 header injection 升级为 desync，而且一部分可由浏览器 `fetch()` 触发。

### Recon 信号

先找**路径/参数可产生响应头或请求头注入**：

```
%0d%0a
%0a
encoded space + HTTP/1.1 + CRLF
```

不要把所有 CRLF injection 都直接判 desync；必须证明连接边界受影响。

### 验证策略

```
CRLF/header injection primitive
  ↓
让后端保持连接
  ↓
注入无害 TRACE/404/HEAD 前缀
  ↓
观察响应队列/下一请求错位
```

2026 研究表明 HEAD technique、100-continue 等可帮助观察盲 tunnelling/desync，但这些属于**高级验证**，优先在 HTB/本地靶场使用。

---

## 8. 2026：HTTP Terminator / Multipart Byteranges Differential

新研究发现部分实现会错误把 request 的：

```
Content-Type: multipart/byteranges; boundary=...
```

按 response-oriented multipart/byteranges 语义处理，造成新的 request boundary differential。

**状态：RESEARCH-GATED。** 这不是“见到 multipart/byteranges 就有漏洞”。

测试思路：

```
POST body使用multipart/byteranges结构
  ↓
在可疑 terminator 后放无害下一请求 marker
  ↓
比较前端/后端是否消费相同字节数
```

优先用最新 Burp/Turbo Intruder 方法；不要在 skill 里硬编码一个“通杀 payload”。

---

## 9. 从确认 Desync 到 Web Shell

可利用影响常见：

```
绕过前端ACL/WAF
内部路径访问
poison下一用户请求
response queue poisoning
cache poisoning
credential capture
```

`/web-attack` 的目标是 Shell，因此拿到 auth/admin 后继续找：

```
admin upload/plugin/theme editor
CI/build command
server-side template
internal debug/RCE endpoint
```

确认 desync 但不能继续到 Shell → 漏洞成立，但本模块 success condition 尚未达成。

---

## 10. 操作注意

- HTB/CTF 可做跨请求验证；生产授权环境优先单用户/无害 marker。
- 不要用会长期污染共享 cache/队列的 payload 作为第一验证。
- 记录原始 request/response、连接模式、H1/H2、重复次数。
