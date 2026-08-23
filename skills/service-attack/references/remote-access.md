# Remote Access Services — SSH / WinRM / RDP / VNC

此 reference 主要处理“已经有有效认证材料，直连服务如何形成 host access”。口令猜测/喷洒不在这里。

---

## SSH

```bash
ssh USER@TARGET
ssh -i KEY USER@TARGET
```

成功后立即记录：

```bash
id
hostname
uname -a
```

SSH chain 在“获得稳定 shell”处闭环；不要在本 reference 复制整套 Linux 本地提权。

---

## WinRM

```bash
evil-winrm -i TARGET -u USER -p 'PASS'
# 或证书/Hash等已获认证材料对应方式
```

验证：

```powershell
whoami
hostname
```

获得 PowerShell remote shell 即成功。

---

## RDP

```bash
xfreerdp /v:TARGET /u:USER /p:'PASS' /cert:ignore
```

NLA/CredSSP/RestrictedAdmin 等模式依赖凭据类型和目标配置；不要把“TCP 3389 open”当登录能力。

---

## VNC

已有密码或明确无认证时：

```bash
vncviewer TARGET::5900
```

成功 = 获得交互桌面。不要在此 reference 做 brute force。

---

## Telnet

仅对遗留设备/网络设备：

```bash
telnet TARGET 23
```

成功认证后记录权限级别和 CLI prompt；配置修改前备份 running config/原值。
