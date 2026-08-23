# Multi-hop Pivoting

## 1. 规划表

```text
Hop 1: operator → pivot-A → subnet-A
Hop 2: via subnet-A → pivot-B → subnet-B
Hop 3: ...
```

每跳记录：

```text
agent/session ID
remote interfaces
route added
forward/listener
return path
cleanup command
```

## 2. 原则

优先用 Ligolo-ng 多 session/TUN 路由表达网段；只有工具/协议限制时才叠 SOCKS + proxychains + port forward。

## 3. 检查路由冲突

```bash
ip route
ip rule
```

避免目标内网网段和 operator 本地/VPN 网段冲突。冲突时可选择更具体 route、namespace、独立 TUN 或单端口 forward。

## 4. 验证每一跳

```bash
nc -vz DEST PORT
curl -m 5 http://DEST:PORT/
```

每增加一跳先验证，再继续下一跳。
