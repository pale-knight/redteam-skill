# Chisel / GOST v3

## 1. Chisel

官方定位：TCP/UDP tunnel over HTTP，使用 SSH 协议保护。

### Server

```bash
chisel server --reverse --port 8080
```

### Reverse SOCKS

```bash
chisel client OPERATOR:8080 R:socks
```

### Reverse port forward

```bash
chisel client OPERATOR:8080 R:8443:127.0.0.1:443
```

具体 ACL/auth 参数随版本变化，使用前 `chisel --help`；如果启用 authfile/ACL，确认版本已包含对应安全修复。

## 2. GOST v3

不要再以旧 `ginuerzh/gost v2` 作为唯一文档源。当前主项目为 `go-gost/gost` v3。

安装：

```bash
git clone https://github.com/go-gost/gost.git
cd gost/cmd/gost
go build
./gost -V
```

GOST v3 可以组合：

```text
SOCKS4/5
HTTP/HTTPS
SSH
WebSocket
HTTP2/HTTP3
QUIC
TUN/TAP
TCP/UDP forward
reverse tunnel
multi-hop forwarding chain
```

由于 v3 配置语法丰富且持续变化，实战时优先按当前 `gost -h` 和官方 `gost.run` 对所需 transport 生成最小配置，不在 Skill 中伪造一套“一条命令通用所有版本”的参数。

## 3. 选型

```text
full subnet + scanner friendliness → Ligolo-ng
simple HTTP egress / reverse socks→ Chisel
complex protocol chain / QUIC/H3 → GOST v3
```
