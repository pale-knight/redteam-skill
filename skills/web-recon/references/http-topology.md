# HTTP / Proxy / Cache / Parser Boundary Recon

> 用于在进入 HTTP Desync、Web Cache、Parser Differential 前建立“请求经过哪些组件”的基线。这里只做低风险差异观察，不在 recon 阶段做跨用户 desync/poison 利用。

---

## 1. HTTP 协议支持

```
curl -skI --http1.1 https://TARGET/
curl -skI --http2 https://TARGET/
```

TLS ALPN：

```
openssl s_client -connect TARGET:443 -servername TARGET -alpn 'h2,http/1.1' </dev/null 2>/dev/null | grep -i 'ALPN protocol'
```

记录：

```
客户端→前端是否H2
后端可能是否HTTP/1.1（从Server/Via/已知架构推断）
是否Alt-Svc h3
```

HTTP/2 前端 + HTTP/1.1 后端是 H2.CL/H2.TE 等差异的重要信号，但不是漏洞证据。

---

## 2. CDN / WAF / Reverse Proxy 指纹

```
curl -skI https://TARGET/ | grep -Ei \
'^(server|via|x-cache|x-served-by|x-varnish|cf-ray|cf-cache-status|x-amz-cf|x-akamai|x-sucuri|x-envoy|x-forwarded|alt-svc):'
```

结合：

```
wafw00f https://TARGET
whatweb https://TARGET
```

不要只根据一个 Header 下结论；`Server` 可能被伪装或来自前端代理。

---

## 3. Cache 基线

连续请求同一资源：

```
for i in 1 2 3; do
  curl -skI "https://TARGET/static/app.js?cb=baseline" | \
    grep -Ei '^(age|x-cache|cf-cache-status|via|cache-control|vary|etag|last-modified):'
  sleep 1
done
```

看：

```
Age增长
MISS → HIT
X-Cache: HIT
CF-Cache-Status: HIT
ETag/Last-Modified
Cache-Control
Vary
```

无明显 Header 也不代表没有内部 cache。

---

## 4. Cache Key 初步差异

Recon 阶段只做无害 marker：

```
# Query是否进key
curl -skI 'https://TARGET/resource?cb=one'
curl -skI 'https://TARGET/resource?cb=two'

# Host派生header是否影响响应（不要在公共目标上污染共享cache）
curl -skI https://TARGET/ -H 'X-Forwarded-Host: recon.invalid'
curl -skI https://TARGET/ -H 'X-Original-URL: /recon-marker'
```

若响应体/Location/绝对 URL 随某个 header 变化，而 cache key 看起来不包含该 header → 记录 `/web-attack web-cache.md` 候选。

---

## 5. Path Normalization / Delimiter 基线

选一个**无状态、不会写数据**的已知路径，比如 `/robots.txt` 或静态文件：

```
/robots.txt
/robots.txt/
/robots.txt;x
/robots.txt?x=1
/robots.txt%3Fx
/robots.txt%23x
/robots.txt%3Bx
```

比较：

```
status
Content-Length
Location
Cache headers
backend error page
```

如果前端与后端对 `; ? # encoded delimiter / normalization` 看法不同，记录为 Cache/Parser Differential 候选。

---

## 6. Content-Type / Parser Surface

从正常请求记录：

```
application/x-www-form-urlencoded
application/json
multipart/form-data
application/xml
text/xml
application/graphql
application/grpc-web
```

同一 endpoint 支持多个 body parser → `/web-attack parser-differentials.md` 高优先级。

---

## 7. 输出给 /web-attack

```
Front-end/CDN/WAF:
Reverse proxy:
Likely backend server/framework:
Client-side HTTP: H1/H2/H3
Cache indicators:
Vary:
Path normalization anomalies:
Multiple body parsers:
Headers that change response:
Potential boundary:
```
