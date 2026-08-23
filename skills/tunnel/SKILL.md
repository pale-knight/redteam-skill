---
name: tunnel
description: "Network reachability and pivoting after an operator already has a foothold. Use to make previously unreachable hosts, subnets, services or listener directions reachable via Ligolo-ng, Chisel, GOST v3, SSH/native forwarding, socat/netsh, Microsoft Dev Tunnels, DNS/HTTP/QUIC fallback transports, and multi-hop routing. This module does not exploit services, obtain credentials, or own C2/persistence. Its success condition is changed reachability: the operator can route/connect to the intended internal network/service through the selected foothold."
---

# /tunnel — Network Reachability & Pivoting

> **定位：** 已有 foothold 之后，把“原本不可达的 IP/Port/Network”变成可达。
>
> 不负责扫描/漏洞利用；不负责长期 C2/persistence；不把所有“隐蔽通信”都塞进 tunnel。

---

## 开局与收尾

开局第一件事：Read `./notes.md`。没有则 `python ~/.claude/skills/bin/notes.py init`。只按已拿下/凭据继续。
走到哪条链，才 Read **一份** `references/<file>.md`。禁止开局全读、禁止凭记忆写 payload。
监听 / sudo / 输密码 / Permission denied：立刻停，说明等操作者做什么，等回报。不要假装已成功。
收尾：
1. 追加 `./notes.md`
2. `python ~/.claude/skills/bin/modules.py tail <本模块名>`
   Read 备用：`~/.claude/skills/shared/modules.yaml`
   禁止 `./modules.yaml` 和 `python ../bin/...`
3. 优先 `default_next`；`never_default` 不得当作默认（操作者点名除外）
4. 名册外的名字不许建议
5. 停。等操作者选 `/模块` 或 `/clear`
`/edr-bypass` 半条链未完：打通后回本模块，不要 /clear。


---

## 0. 输入

```text
Foothold host
operator reachable addresses
foothold interfaces/routes/DNS
required destination subnet/port
outbound constraints
inbound constraints
privilege level
```

先明确你需要的是：

```text
full subnet routing
single TCP/UDP forward
reverse forward
SOCKS proxy
multi-hop pivot
temporary public exposure of a local service
```

---

## 1. P0：Ligolo-ng

现代默认首选之一。官方当前支持 TUN、TCP/UDP/ICMP、多 agent、多 tunnel、listener/bind、自动恢复；0.8+ 还加入 Web UI/API、daemon、auto-bind、autoroute，当前 release 已到 0.9.x。

适合：

```text
完整内网网段
直接使用 nmap/curl/smb/ssh 等工具
不想全局 proxychains
多 hop
```

详见 `references/ligolo-ng.md`。

---

## 2. HTTP/受限出口：Chisel / GOST v3

### Chisel

单文件、TCP/UDP over HTTP + SSH security，适合严格 HTTP egress 和单/少量 forward。

### GOST v3

当前 go-gost/gost v3 支持 TCP/UDP、SOCKS、HTTP/2/3、QUIC、WebSocket、SSH、TUN/TAP、多级转发链和反向代理，适合复杂 transport 组合。

详见 `references/chisel-gost.md`。

---

## 3. Native SSH / OS forwarding

如果已经有 SSH/系统能力，不必为了“最新”额外投放工具：

```text
ssh -L / -R / -D
ProxyJump
socat
netsh interface portproxy
```

详见 `references/native-forwarding.md`。

---

## 4. Microsoft Dev Tunnels / legitimate tunnel services

Microsoft Dev Tunnels 原本用于把 localhost/web services 临时暴露到 Internet。对授权红队来说，可以作为**网络可达性**候选：

```text
internal/local service
→ Dev Tunnel relay
→ external operator reachability
```

如果某工具进一步把 Dev Tunnels 做成完整 C2/RPC implant，那部分属于 `/post` 的 C2/OPSEC，不在 `/tunnel` 维护。

详见 `references/dev-tunnels.md`。

---

## 5. Fallback transports

当标准 TCP/HTTP egress 不可用，再考虑：

```text
DNS / DoH
WebSocket
HTTP2/HTTP3
QUIC
ICMP (environment dependent)
```

这些是 transport fallback，不等于“越隐蔽越好”。优先选择稳定、可诊断、对目标网络影响可控的路径。

详见 `references/fallback-transports.md`。

---

## 6. Multi-hop

每一跳都要记录：

```text
pivot identity
reachable subnet
return path
route installed
listener/forward dependency
failure domain
```

不要把 3 跳网络做成一串不可恢复的一次性命令。

详见 `references/multi-hop.md`。

---

## 7. 成功判断

```text
Before: operator cannot connect to DEST
After : operator can establish required TCP/UDP/application connection to DEST
```

例：

```bash
nc -vz 10.20.30.40 445
curl -k https://10.20.30.40:8443/
```

不要把“agent connected”当成 tunnel 成功；必须验证目标网络/service 真正可达。

## 完成后

写入 `./notes.md`。候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。
