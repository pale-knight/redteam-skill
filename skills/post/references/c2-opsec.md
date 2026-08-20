# C2 通道 OPSEC

> **TECH：** implant 如何稳定、可诊断地回到操作者  
> **不是：** 免杀手册、通杀 EDR、Workers 开发教程  
> payload 被杀 → `/edr-bypass` 再回 `/post`

---

## 分层

```text
目标 implant
    → redirector（独立 VPS / CDN / HTTPS 反代）
        → teamserver（只对操作者/redirector 开放）
```

```text
错误：目标直接连 sliver-server 公网 IP:8888
正确：目标只连看起来像 SaaS 的 HTTPS 主机名
```

域前置 / CloudFront / Cloudflare 可以作为 **redirector**，配置随厂商变，以当前 CDN 文档为准，不在这里贴过期 Workers 脚本。

Microsoft Dev Tunnels：只把端口暴露出去 = `/tunnel`。某工具把 Dev Tunnels 做成 implant 控制面 = 本模块的一种 **channel**，仍要满足「回连成功」。

---

## 选传输

主机画像里出网结果：

```text
443 通           → HTTPS beacon
仅 80            → HTTP
HTTP(S) 全拦     → DNS/DoH（慢、小）
TCP 全死         → 先不要 ICMP C2；评估 /tunnel fallback 或换入口
```

ICMP/dnscat 当 C2 噪声和稳定性都差，不是默认。

---

## Sleep / 工作时间

```text
beacon seconds 60–300，jitter 20% 起
交互短窗再切 session 或把 sleep 临时降下来
能设工作时间就设（工作日营业时段），减少夜间回连
```

Sliver：`--seconds` `--jitter`。具体 profile 语法随版本看 `--help`。

---

## 证书与域名

HTTPS listener 用合法证书（Let’s Encrypt 在 **redirector** 上）。自签也能上线，更容易被拦截。域名不要用 `c2`/`update-check` 这种。

---

## 失败分流

```text
完全无回连 + 防火墙/代理日志拒绝     → 换端口/HTTPS/DNS（仍 /post）
落地瞬间被隔离 / beacon 进程被杀     → /edr-bypass → 回 /post 再 generate
能上线立刻掉                         → sleep 过短或主机休眠；先画像
```

不要把「场上有 CrowdStrike」写成不能 C2。
