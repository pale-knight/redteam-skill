# Campaign Validation / Result Tracking

## 1. 每条链都必须有技术成功判据

```text
credential path → credential validated
AiTM            → session validated against target resource
device code     → token + resource access
consent         → delegated grant + API access
remote support  → interactive remote session
client exec     → marker/command execution + optional shell foothold
```

## 2. 记录防护平面

```text
MAIL        mail gateway / DMARC / Safe Links
BROWSER     download/reputation/MOTW
IDENTITY    MFA/FIDO/CA/token protection
ENDPOINT    AV/EDR/AMSI/WDAC/AppLocker/memory scan
```

只有 `ENDPOINT` 这一层在执行阶段阻断，才提示操作者可以选择 `/edr-bypass`。

## 3. 清理

结束后按实际使用链清理：

```text
lure domains/subdomains
OAuth apps/consents
remote-support sessions
staged files
phishing infrastructure
captured test sessions/tokens
```
