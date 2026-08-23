# Fallback Transports

## 1. 只在真实网络约束需要时用

```text
DNS / DoH
WebSocket
HTTP2/HTTP3
QUIC
ICMP
```

## 2. DNS

`dnscat2` 类方案仍可用于只有 DNS 路径的受限网络，但带宽低、检测面明显，不应作为现代默认首选。

## 3. HTTP2/HTTP3 / QUIC

GOST v3 等工具已经支持现代 transport，可用于企业代理/防火墙环境的兼容性测试。先确认代理、TLS inspection 和 UDP/443 可达性。

## 4. 成功判据

不要以“tunnel process running”判断成功；必须验证最终 destination service 真的可达。
