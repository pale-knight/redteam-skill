# 数据库 / Data Store — 只读枚举

不尝试默认口令或 brute force。只有匿名访问或已掌握凭据时深入。

---

## MSSQL — 1433

```bash
nmap -Pn -sV -p 1433 --script ms-sql-info,ms-sql-ntlm-info TARGET
impacket-mssqlclient 'DOMAIN/USER:PASS@TARGET' -windows-auth
```

登录后：

```sql
SELECT @@VERSION;
SELECT SYSTEM_USER, USER_NAME();
SELECT IS_SRVROLEMEMBER('sysadmin') AS is_sysadmin;
SELECT * FROM sys.server_permissions WHERE grantee_principal_id = SUSER_ID();
SELECT name,product,provider,data_source,is_linked FROM sys.servers;
SELECT name,value_in_use FROM sys.configurations WHERE name IN ('xp_cmdshell','Ole Automation Procedures','clr enabled','external scripts enabled');
```

重点记录：sysadmin/CONTROL SERVER/IMPERSONATE、Linked Server、服务账号线索、执行功能状态。

---

## MySQL / MariaDB — 3306

```bash
nmap -Pn -sV -p 3306 --script mysql-info TARGET
mysql -h TARGET -u USER -p
```

```sql
SELECT VERSION(), USER(), CURRENT_USER(), @@hostname, @@version_compile_os;
SHOW GRANTS;
SHOW DATABASES;
SHOW ENGINES;
SELECT @@secure_file_priv, @@global.general_log, @@global.general_log_file, @@plugin_dir;
SELECT User,Host,plugin FROM mysql.user;
```

记录：FILE、SYSTEM_VARIABLES_ADMIN/legacy SUPER、CREATE SERVER、plugin_dir、FEDERATED。

---

## PostgreSQL — 5432

```bash
nmap -Pn -sV -p 5432 TARGET
psql -h TARGET -U USER -d postgres
```

```sql
SELECT version(), current_user, current_database();
\du+
SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolreplication FROM pg_roles;
SELECT pg_has_role(current_user,'pg_execute_server_program','MEMBER') AS exec_program,
       pg_has_role(current_user,'pg_read_server_files','MEMBER') AS read_files,
       pg_has_role(current_user,'pg_write_server_files','MEMBER') AS write_files;
SELECT extname, extversion FROM pg_extension;
```

`COPY PROGRAM` 与文件角色是不同能力，不要把 `pg_read_server_files` 当执行权限。

---

## Oracle — 1521

```bash
nmap -Pn -sV -p 1521 --script oracle-tns-version TARGET
odat sidguesser -s TARGET
sqlplus 'USER/PASS@//TARGET:1521/SERVICE'
```

```sql
SELECT * FROM SESSION_PRIVS ORDER BY PRIVILEGE;
SELECT USER FROM dual;
SELECT * FROM USER_DB_LINKS;
SELECT owner,job_name,job_type,enabled FROM ALL_SCHEDULER_JOBS FETCH FIRST 50 ROWS ONLY;
```

重点：CREATE JOB / CREATE EXTERNAL JOB / Java权限 / DB Link。

---

## Redis / Valkey-like — 6379

```bash
redis-cli -h TARGET PING
redis-cli -h TARGET INFO server
redis-cli -h TARGET INFO replication
redis-cli -h TARGET ACL WHOAMI
redis-cli -h TARGET COMMAND INFO EVAL EVALSHA RESTORE MODULE CONFIG
redis-cli -h TARGET CONFIG GET protected-mode
redis-cli -h TARGET CONFIG GET dir
redis-cli -h TARGET CONFIG GET dbfilename
redis-cli -h TARGET SCAN 0 COUNT 100
```

`KEYS *` 在大库可能造成明显负载，Recon 默认使用 `SCAN`。

记录：版本、auth/ACL、Lua/RESTORE/MODULE capability、replica role、文件路径、modules。

---

## MongoDB — 27017

```bash
nmap -Pn -sV -p 27017 --script mongodb-info TARGET
mongosh --host TARGET
```

```javascript
db.hello()
db.runCommand({connectionStatus:1})
db.adminCommand({listDatabases:1, nameOnly:true})
```

有权限后：

```javascript
show dbs
use app
show collections
db.serverStatus().version
```

不要把 `mongosh` 的 Node.js 环境与服务器端 JavaScript 混为一谈；不使用旧 `db.eval("child_process...")` 伪通用 RCE。

---

## Elasticsearch / OpenSearch — 9200

```bash
curl -s http://TARGET:9200/
curl -s http://TARGET:9200/_cat/indices?v
curl -s http://TARGET:9200/_security/_authenticate 2>/dev/null
```

记录 cluster/version、security plugin、anonymous/read scope。

---

## CouchDB — 5984

```bash
curl -s http://TARGET:5984/
curl -s http://TARGET:5984/_all_dbs
curl -s http://TARGET:5984/_session
```

---

## Cassandra — 9042

```bash
cqlsh TARGET 9042
```

连接成功后：

```sql
DESCRIBE CLUSTER;
DESCRIBE KEYSPACES;
SELECT role,can_login,is_superuser FROM system_auth.roles;
```

---

## Neo4j — 7687 / 7474

```bash
cypher-shell -a neo4j://TARGET:7687 -u USER -p PASS 'SHOW CURRENT USER'
cypher-shell -a neo4j://TARGET:7687 -u USER -p PASS 'SHOW DATABASES'
```
