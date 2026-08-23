---
name: shell
description: "Shell and session operations after an attack module already established command execution, a raw shell, webshell channel, container/runner shell, or remote session. This module does not own exploitation and should not pull SSH/WinRM/RDP authentication or vulnerability-to-shell chains out of Web/AD/Cloud/K8s/CI-CD/Service/Phishing. Use it to bootstrap a usable callback from existing command execution, stabilize Linux PTY, upgrade Windows sessions with ConPTY where applicable, manage listeners, recover fragile sessions, and exchange files for continued operations."
---

# /shell — Shell & Session Operations

> **新定位：** 不负责“把漏洞变成 shell”。Attack 模块已经负责把自己选择的链做到 foothold。`/shell` 只处理**已有 execution/shell/session 的质量与可操作性**。

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

## 0. 输入条件

至少满足一个：

```text
single-command execution
raw reverse shell
bind shell
webshell command channel
container/runner shell
poor cmd/PowerShell channel
existing interactive remote session
```

如果你只有一个 Web/AD/Service/Cloud/K8s/CI-CD 漏洞候选，还没有执行能力，回原 Attack 模块继续，不要用 `/shell` 代替 exploit chain。

---

## 1. Session bootstrap

当原 Attack 模块已经证明 single-command execution，但当前 operator 明确选择 `/shell` 来改善会话时，可以从现有 execution primitive 建立 callback。

这不改变攻击链所有权：最终 foothold 仍属于原模块。

见 `references/session-bootstrap.md`。

---

## 2. Linux PTY

目标：

```text
raw /bin/sh
→ PTY
→ Ctrl-C / job control
→ correct TERM/rows/cols
→ stable interactive shell
```

见 `references/linux-pty.md`。

---

## 3. Windows ConPTY / Session Upgrade

目标：把 poor cmd/PowerShell/stdin-stdout channel 变成可正常交互的 Windows session。优先使用系统自带 Pseudo Console 能力；ConPtyShell 是常见实现之一，但不是唯一答案。

见 `references/windows-conpty.md`。

---

## 4. Listener & Recovery

处理：

```text
listener discipline
socket reconnect
TTY state corruption
Ctrl-C breakage
stale session
resume after network interruption
```

见 `references/listeners-recovery.md`。

---

## 5. File Exchange

用于**foothold 日常工具/文件交换**：

```text
HTTP
SMB
SCP/SFTP when already available
base64/chunking
native PowerShell/curl/certutil alternatives where appropriate
```

不负责“大规模数据外带”，那属于 `/post`。

见 `references/file-transfer.md`。

---

## 6. 明确不属于 /shell

```text
SQLi→xp_cmdshell→shell            → /web-attack
MSSQL direct exploit→shell        → /service-attack
PTH/PsExec/WinRM lateral shell    → /ad-attack
Cloud IAM→SSM/VM RunCommand shell → /cloud-attack
K8s exec/container/node shell     → /k8s
Runner workflow→runner shell      → /cicd
ClickFix/client execution→shell   → /phishing
AV/EDR blocks payload             → /edr-bypass
network pivot                     → /tunnel
```

---

## 7. 成功条件

```text
Linux:
[+] PTY usable
[+] Ctrl-C/job control works
[+] TERM + rows/cols correct

Windows:
[+] stable cmd/PowerShell/ConPTY
[+] stdin/stdout/stderr usable
[+] long-running commands do not kill session

Generic:
[+] reliable file exchange
[+] session survives normal operator interaction
```

## 完成后

写入 `./notes.md`。候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。
