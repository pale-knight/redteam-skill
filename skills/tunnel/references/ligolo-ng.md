# Ligolo-ng 0.8/0.9+ Workflow

## 1. 官方能力

Ligolo-ng 使用 TUN interface，不需要 SOCKS/proxychains；agent 端通常不需要管理员权限，proxy/relay 端需要创建 TUN。

## 2. 安装

从官方 releases 获取匹配版本：

```text
proxy/relay: Linux/Windows/macOS/BSD
agent      : target OS/arch
```

先看当前帮助：

```bash
./proxy -h
./agent -h
```

0.8+ CLI/配置与旧教程已有差异，优先遵循当前官方 docs，不把老 `session/start` 语法硬编码为唯一方式。

## 3. Linux relay TUN

手工方式仍可使用：

```bash
sudo ip tuntap add user $(whoami) mode tun ligolo
sudo ip link set ligolo up
```

0.8+ 可优先使用 autoroute/自动 interface 管理能力（按当前版本 UI/CLI）。

## 4. Agent connection

实验环境可使用自签证书；真实授权环境优先验证 certificate fingerprint 或使用受控证书，避免长期 `-ignore-cert` 形成错误习惯。

```text
agent → relay/proxy TLS connection
→ select agent
→ inspect remote interfaces/routes
→ add/autoroute subnet
→ start tunnel
```

## 5. 验证

```bash
ip route
nc -vz INTERNAL 445
curl http://INTERNAL:8080/
```

Ligolo-ng 支持 TCP、UDP 和 ICMP echo；不同扫描类型仍受 userland stack/transport 特性影响。

## 6. Reverse listener / bind

当内网服务只能由 pivot 主机发起或需要 callback forwarding，可使用 Ligolo listener/bind 功能。命令语法按当前 0.9.x `help`/Web UI 为准。

## 7. Multi-hop

第二跳 agent 的回连可以走第一跳已经建立的 reachability，再给第二层网段增加新 route。每层记录独立 session 和 route，避免误删第一跳导致全链断开。
