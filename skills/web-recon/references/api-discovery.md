# API 攻击面枚举详细参考

> 本文件只负责 **HTTP/HTTPS 应用层 API attack surface discovery**。发现越权/注入/认证差异候选后交 `/web-attack`，不在这里继续手工利用。

---

## 1. 先找规范文件

常见路径：

```
/swagger.json
/swagger/v1/swagger.json
/swagger-ui.html
/swagger-ui/
/api-docs
/v1/api-docs
/v2/api-docs
/v3/api-docs
/openapi.json
/openapi.yaml
/.well-known/openapi.json
/docs
/redoc
```

快速：

```
ffuf -w /usr/share/seclists/Discovery/Web-Content/api/api-docs.txt \
  -u https://TARGET/FUZZ -mc 200,301,302,401,403
```

拿到 OpenAPI/Swagger 后记录：

```
method
path
path/query/header/cookie/body 参数
required/optional
securitySchemes
requestBody schema
response schema
admin/internal/debug/tag
```

不要只看文档 UI，直接保存原始 JSON/YAML。

```
curl -sk https://TARGET/openapi.json -o openapi.json
```

Nuclei 可以直接把规范当输入：

```
nuclei -l openapi.json -im openapi -severity critical,high
nuclei -l swagger.json -im swagger -tags cve,misconfig
```

---

## 2. Kiterunner — Contextual Route Discovery

普通目录字典只猜 path；Kiterunner route 包含 method/header/path/query/body 形态，适合 Flask/Rails/Express/Django 等显式路由框架。

### 字典

```
kr wordlist list
```

单目标先低并发：

```
kr scan https://TARGET \
  -A=apiroutes-210228:20000 \
  -x 5 \
  --fail-status-codes 400,404,501,502,426,411
```

注意：默认示例常把 401/403 当失败码，但红队/CTF 场景里 **401/403 本身就是端点存在证据**。需要发现受保护管理路由时，不要把它们过滤掉。

已有编译路由表：

```
kr scan https://TARGET -w routes.kite -x 5
```

API 基路径已知：

```
kr scan https://TARGET/api/ -A=apiroutes-210228:20000 -x 5
```

### 结果判断

```
200  → 真实路由，记录响应结构
201  → 可能误触发写操作；停止批量重放，人工检查
204  → 常见成功但无body
301/302 → 看Location是否暴露真实路由
401  → 路由存在，需要认证
403  → 路由存在，可能BFLA/来源限制
405  → path存在，但method不对；必须做method矩阵
```

如果路由扫描可能修改状态，降低并发并优先只做 GET/HEAD；对 POST/PUT/PATCH/DELETE 进入 `/web-attack` 前人工确认。

---

## 3. Method Matrix

发现一个重要 path 后测试：

```
OPTIONS /api/v1/users
GET     /api/v1/users
HEAD    /api/v1/users
POST    /api/v1/users
PUT     /api/v1/users
PATCH   /api/v1/users
DELETE  /api/v1/users
```

命令：

```
for m in GET POST PUT PATCH DELETE OPTIONS HEAD; do
  echo "=== $m ==="
  curl -sk -o /dev/null -D- -X "$m" https://TARGET/api/v1/users | head
 done
```

关注：

```
GET 401 但 POST 200
/v2/admin 403 但 /v1/admin 200
DELETE 只校验cookie、不校验Bearer
OPTIONS泄露 Allow: PUT,DELETE
```

发现差异 → `/web-attack` BFLA/BOLA/auth bypass。

---

## 4. API Version / Shadow / Deprecated Endpoint

同资源做版本矩阵：

```
/api/v0/users
/api/v1/users
/api/v2/users
/api/v3/users
/api/beta/users
/api/alpha/users
/api/legacy/users
/api/old/users
/api/deprecated/users
/api/internal/users
/api/private/users
/api/mobile/users
/api/partner/users
```

路径词：

```
admin
internal
private
debug
test
staging
dev
legacy
old
beta
mobile
partner
management
actuator
metrics
health
```

旧版本常见问题不是“代码更老”这么简单，而是：

```
新版加了鉴权，旧版没加
新版限制字段，旧版Mass Assignment仍接受
新版修了IDOR，mobile/partner API没同步
新版禁用debug，旧路由仍存活
```

这里只确认端点存在；漏洞验证交 `/web-attack`。

---

## 5. 从流量反建 API

已经能正常浏览应用时，浏览器/Burp 流量往往比字典更准。

### mitmproxy2swagger

将正常使用应用产生的流量保存后，反建 OpenAPI，再比较未访问到的资源/参数。

典型用途：

```
浏览器正常操作
  ↓
Burp/mitmproxy capture
  ↓
mitmproxy2swagger
  ↓
OpenAPI inventory
  ↓
补 Kiterunner / 方法 / 版本枚举
```

---

## 6. GraphQL Discovery

常见：

```
/graphql
/graphiql
/playground
/api/graphql
/v1/graphql
/query
/gql
/graphql/console
```

确认：

```
curl -sk -X POST https://TARGET/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ __typename }"}'
```

返回类似：

```
{"data":{"__typename":"Query"}}
```

→ GraphQL。

Recon 记录：

```
是否需认证
是否允许introspection
是否有GraphiQL/Playground
是否使用GET执行query/mutation
是否WebSocket subscription
```

真正字段枚举、BOLA、batch、alias、mutation auth → `/web-attack references/api-security.md`。

### GQLHound — 被动反建真实 GraphQL 操作

适用：已经通过 Burp 正常浏览/操作应用，尤其是 introspection 被关闭、前端使用 persisted/复杂 operation 时。

GQLHound 不主动猜 schema，而是从 Proxy/Repeater 流量中记录：

```text
operation name / type
query / mutation / subscription
variables 路径与不同 shape
真实 Cookie / Authorization / Header
batched mutation
inline vs parameterized query style
```

构建/安装：

```bash
git clone https://github.com/sentient-zero/GQLHound.git
cd GQLHound
gradle wrapper --gradle-version 8.12
./gradlew jar
# 输出：build/libs/gql-hound-2.0.1.jar（版本变化时以实际 build/libs 为准）
```

Burp：

```text
Extensions → Installed → Add → Java → 选择 gql-hound-*.jar
```

使用：

```text
1. 正常浏览目标并走完整业务流程
2. 打开 GQL Hound tab
3. 按 operation / mutation 排序
4. 查看每个 operation 的 variable shapes 和样例值
5. 将高价值 mutation/变量送 Repeater/Intruder
```

重点：

```text
同一 operation 出现多个 variable shape
低权限页面却观察到 admin/billing/export mutation
inline 与 parameterized 两种形式都出现
batched mutation
ID / userId / accountId / role / ownerId / tenantId
```

这些是攻击面，不在 recon 阶段直接判定漏洞。输出给 `/web-attack references/api-security.md`。

### GraphQL Cop — 自动安全候选扫描

适用：已确认 GraphQL endpoint，希望像 nuclei 一样先扫常见 GraphQL 安全问题，再由 `/web-attack` 手工验证。

安装：

```bash
git clone https://github.com/dolevf/graphql-cop.git
cd graphql-cop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

基础扫描：

```bash
python3 graphql-cop.py -t https://TARGET/graphql
```

带认证并经 Burp：

```bash
python3 graphql-cop.py \
  -t https://TARGET/graphql \
  -H '{"Authorization":"Bearer TOKEN"}' \
  -x http://127.0.0.1:8080 \
  -o json
```

查看全部测试：

```bash
python3 graphql-cop.py -l
```

若靶场/授权环境不允许 DoS 类压力测试，先用 `-l` 查看测试 ID，再用 `-e` 排除 alias/field/directive/circular 等资源消耗型检查。

重点候选：

```text
Introspection
GraphiQL / Playground
Field Suggestions
GET query / GET mutation
URL-encoded POST query
Tracing/Debug
Alias/Batch/Field duplication（仅允许时验证资源影响）
```

GraphQL Cop 的阳性结果只是候选；认证绕过、BOLA/BFLA、mutation 越权仍交 `/web-attack` 手工验证。

---

## 7. gRPC / gRPC-Web Discovery

HTTP 页面/JS 出现：

```
application/grpc
application/grpc-web
/grpc.reflection
*.proto
grpc-web-text
```

记录服务名/方法名线索。若是独立 50051 非HTTP服务，由 `/recon` 处理；若通过当前 HTTP 网关/gRPC-Web 暴露，则继续作为 Web/API attack surface。

---

## 8. WebSocket Discovery

看：

```
ws://
wss://
Upgrade: websocket
Sec-WebSocket-Protocol
/socket.io/
/graphql subscription
```

JS grep：

```
grep -RniE 'wss?://|WebSocket\(|socket\.io|subscriptions-transport-ws|graphql-ws' js-output/
```

记录：

```
URL
subprotocol
Cookie/Bearer是否带入
消息格式(JSON/protobuf/custom)
初始认证消息
```

攻击交 `/web-attack references/api-security.md`。

---

## 9. SOAP / WSDL Discovery

发现以下信号时加入 API inventory：

```text
.asmx
?wsdl
application/soap+xml
text/xml + SOAPAction
/ws/ /services/ /soap/
System.Web.Services
```

```bash
curl -sk 'https://TARGET/service.asmx?WSDL' -o service.wsdl
grep -Ei 'operation|soapAction|complexType|element name=' service.wsdl
```

记录：

```text
service / port
operation
SOAPAction
input/output schema
authentication
URL/file/XML参数
legacy/admin operation
```

只做 attack surface mapping；XXE、SOAPAction/body differential、未授权 operation 等交 `/web-attack references/api-security.md`。

---

## 10. 输出给 /web-attack 的最小数据集

```
Endpoint:
Method:
Status baseline:
Authentication:
Parameters:
Request Content-Type:
Response Content-Type:
Object ID / tenant ID:
Version:
Possible legacy route:
Source: Swagger / JS / Kiterunner / history / crawler
Interesting signal: 401/403/405/500/stack trace/schema leak
```
