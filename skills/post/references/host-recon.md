# 妥协后主机画像

> **TECH：** Quiet 本地侦察，给 C2/持久化/外带选路  
> **成功：** notes 里有身份、会话、出网、防御产品、是否域成员  
> **不是：** BloodHound、winPEAS、横移扫描（`/ad-recon` `/recon` `/privesc-*`）

---

## Windows

```cmd
whoami
whoami /groups
whoami /priv
hostname
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"Domain"
echo %USERDOMAIN% %USERDNSDOMAIN% %LOGONSERVER%
quser
query session
net session
net share
ipconfig /all
route print
netstat -ano | findstr LISTENING
```

```powershell
Get-CimInstance Win32_ComputerSystem | select Name,Domain,UserName
Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
  select LocalAddress,RemoteAddress,RemotePort,OwningProcess
Get-ItemProperty HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\* |
  select DisplayName | sort DisplayName
```

防御（只记名字，不 bypass）：

```cmd
sc query WinDefend
tasklist | findstr /i "MsMpEng CrowdStrike Sentinel CarbonBlack Elastic Qualys Cybereason"
```

出网粗测（对操作者 C2/redirector，不要扫全网）：

```cmd
nslookup example.com
curl -I https://<REDIRECTOR>
```

---

## Linux

```bash
id; hostname -f; uname -a
cat /etc/os-release
w; last -n 15
ip a; ip r; ss -tlnp
env | grep -Ei 'PROXY|HTTP|DOMAIN'
ls /home
lastlog | head
```

```bash
# 防御/代理产品（有则记下）
ps aux | grep -Ei 'falcon|sentinel|elastic|qualys|wazuh|osquery|crowdstrike' | grep -v grep
systemctl is-active auditd apparmor ufw 2>/dev/null
```

---

## 记进 notes

```text
user / integrity / admin?
domain-joined: yes/no
interactive sessions:
egress 443/DNS: ok/fail
EDR/AV product names:
shares / logged-on others:
candidate persist: HKCU vs HKLM / user systemd vs /etc/systemd
candidate C2 transport: HTTPS / DNS
```

域成员只记事实。枚举用户/GPO/LAPS → `/ad-recon`。
