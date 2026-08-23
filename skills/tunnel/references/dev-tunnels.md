# Microsoft Dev Tunnels / Legitimate Tunnel Services

## 1. 定位

Microsoft Dev Tunnels 用于把本地服务临时暴露到 Internet，并支持访问控制。红队中可把它当作**reachability primitive**，不是默认 C2 框架。

## 2. CLI

安装当前官方 `devtunnel` CLI 后先检查：

```bash
devtunnel --version
devtunnel -h
```

典型合法功能流：

```text
login/authenticate
→ create tunnel
→ add/host local port
→ obtain public tunnel endpoint
→ operator connects
```

命令和 auth model 可能随 preview/GA 变化，因此以当前 Microsoft docs 为准。

## 3. 红队适用场景

```text
foothold only has outbound Microsoft/cloud reachability
need to expose one local/internal web service temporarily
traditional inbound path impossible
```

## 4. 边界

```text
Dev Tunnel used to expose/connect a service → /tunnel
Dev Tunnel used inside a long-lived command-and-control protocol → /post (C2/OPSEC)
```

## 5. 清理

测试后删除 tunnel resource/host process，确认公网 endpoint 不再可达。
