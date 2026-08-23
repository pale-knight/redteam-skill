# Redis / MongoDB / Elasticsearch / CouchDB / Neo4j

---

## Redis — 6379

### 1. Gate

```bash
redis-cli -h TARGET INFO server
redis-cli -h TARGET ACL WHOAMI
redis-cli -h TARGET COMMAND INFO EVAL RESTORE MODULE CONFIG
redis-cli -h TARGET CONFIG GET dir
redis-cli -h TARGET CONFIG GET dbfilename
```

### 2. File-write primitives

经典 SSH/cron/webroot 写入只在以下条件都成立时考虑：

```text
CONFIG write permission
server persistence command available
filesystem path writable by redis process
target actually consumes the written file
```

不要把“Redis未授权”直接等同“能写 /root/.ssh”。

在靶场优先写 `/tmp/redis-marker` 类无害目标；确认后恢复 `dir`/`dbfilename` 原值。

### 3. Module / Replication paths

`MODULE LOAD`、replica/rogue-server 模块传输依赖 Redis 版本、ACL command permissions、module loading policy 和 OS/arch。现代 Redis 已经对这些路径有大量限制；先用 `COMMAND INFO` 和 ACL 判断，再选择已验证工具，不复制“4.x-7.x通用”说法。

### 4. 2025-2026 RCE candidates

```text
CVE-2025-49844 RediShell — authenticated + Lua + vulnerable version
CVE-2026-23479 — authenticated UAF candidate
CVE-2026-25243 — authenticated RESTORE candidate
CVE-2026-25588 — RESTORE + RedisTimeSeries
CVE-2026-25589 — RESTORE + RedisBloom
CVE-2026-23631 — replica/Lua specific
```

这些是 `VERSION / AUTH / MODULE / CONFIG GATED`。只有找到稳定公开 PoC 并确认精确版本后才执行；否则保留为研究候选。

---

## MongoDB — 27017

MongoDB direct-service 重点是**数据/角色/拓扑控制**，不是旧 `db.eval + child_process` 假 RCE。

```javascript
db.runCommand({connectionStatus:1})
db.hello()
show dbs
```

高权限后评估：

```text
user/role administration
replica/shard configuration
backup/snapshot exposure
application secrets stored in collections
version-specific CVE
```

服务器端 JS 是 MongoDB JS engine，不等于 Node.js `mongosh`；不要生成 `require('child_process')` 服务器端利用。

---

## Elasticsearch / OpenSearch — 9200

```bash
curl -s http://TARGET:9200/_security/_authenticate
curl -s http://TARGET:9200/_cat/indices?v
```

攻击链优先：

```text
anonymous/admin API exposure
sensitive index discovery
snapshot repository exposure
script/plugin capability
version-specific RCE candidate
```

只在目标版本明确存在已验证 RCE 时进入 exploit；不要使用历史 Groovy sandbox escape 作为现代通用链。

---

## CouchDB — 5984

```bash
curl -s http://TARGET:5984/_session
curl -s http://TARGET:5984/_all_dbs
```

管理员权限后可验证 DB/user/config write，但先用临时 test DB 并 cleanup；历史 config-based command execution 必须按精确版本确认。

---

## Neo4j — 7687

高权数据库用户重点评估：

```text
APOC availability
custom procedures/plugins
file import/export configuration
credential/data relationships
```

APOC 不是天然 OS-RCE；按实际 procedure allowlist 和版本判断。
