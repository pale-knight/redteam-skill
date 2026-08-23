# Native SSH / socat / netsh Forwarding

## 1. SSH local forward

```bash
ssh -L 127.0.0.1:8443:10.20.30.40:443 user@PIVOT
```

## 2. SSH reverse forward

```bash
ssh -R 0.0.0.0:8080:127.0.0.1:80 user@OPERATOR
```

远端绑定是否允许取决于 `GatewayPorts` 等 sshd 配置。

## 3. SOCKS

```bash
ssh -D 127.0.0.1:1080 user@PIVOT
```

## 4. ProxyJump

```bash
ssh -J user1@PIVOT1 user2@TARGET
```

## 5. socat

```bash
socat TCP-LISTEN:8443,fork,reuseaddr TCP:10.20.30.40:443
```

## 6. Windows netsh portproxy

```cmd
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8443 connectaddress=10.20.30.40 connectport=443
netsh interface portproxy show all
```

清理：

```cmd
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=8443
```

注意 Windows Firewall 仍可能需要对应入站规则；那是 reachability 配置，不是 EDR bypass。
