# Listener / Session Recovery

## 1. Listener 选择

```bash
nc -lvnp 4444
rlwrap nc -lvnp 4444
socat -d -d TCP-LISTEN:4444,reuseaddr,fork STDOUT
```

框架 shell/beacon 使用框架原生 handler，不要为了统一强行套 nc。

## 2. 会话质量诊断

```text
Ctrl-C kills socket?
stdin buffered?
stderr missing?
TTY rows/cols wrong?
long-running command causes timeout?
reverse path blocked intermittently?
```

如果问题是网络可达性，而不是 shell 本身，切 `/tunnel` 或回原 Attack 模块调整 callback transport。

## 3. Recovery

Linux：

```bash
stty sane
reset
```

如果当前 shell 死掉但原 exploit/command channel 仍存在，从原 Attack 模块或 `session-bootstrap.md` 再建立一个新 session。
