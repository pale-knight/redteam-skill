# 常见网络服务 — 只读枚举

原则：无爆破、无写入、无命令执行。已掌握凭据可以用于只读枚举。

---

## SMB — 139/445

```bash
nmap -Pn -sV -p 139,445 --script smb-protocols,smb2-security-mode,smb2-time,smb-os-discovery TARGET
smbclient -L //TARGET/ -N
nxc smb TARGET -u '' -p '' --shares
```

有已知凭据：

```bash
nxc smb TARGET -u USER -p 'PASS' --shares
nxc smb TARGET -u USER -p 'PASS' --users
```

记录：SMB版本、signing、guest/anonymous、hostname/domain、share ACL。

---

## FTP — 21

```bash
nmap -Pn -sV -p 21 --script ftp-syst,ftp-anon TARGET
nc -nv TARGET 21
```

记录：banner、TLS、anonymous、目录是否可列/可写。写入测试留给攻击模块。

---

## SMTP — 25/465/587

```bash
nmap -Pn -sV -p 25,465,587 --script smtp-commands,smtp-ntlm-info TARGET
openssl s_client -starttls smtp -connect TARGET:587 -crlf </dev/null
```

手工：

```text
EHLO recon.local
```

记录：STARTTLS、AUTH mechanisms、relay hints、hostname/domain。VRFY/EXPN 大规模用户名枚举不放 Recon 默认流程。

---

## DNS — 53 TCP/UDP

```bash
dig @TARGET target.com SOA
dig @TARGET target.com NS
dig @TARGET target.com AXFR
nmap -Pn -sU -p 53 --script dns-recursion TARGET
```

AXFR 本身是只读配置检查；成功时记录完整 zone。

---

## NFS / RPC — 111/2049

```bash
rpcinfo -p TARGET
showmount -e TARGET
nmap -Pn -p 111,2049 --script rpcinfo,nfs-showmount,nfs-statfs TARGET
```

只挂载授权只读共享：

```bash
sudo mount -t nfs -o ro,nolock TARGET:/export /mnt/nfs
ls -la /mnt/nfs
```

记录 export、客户端限制、root_squash 线索、可见文件类型。

---

## SSH — 22

```bash
ssh-audit TARGET
nmap -Pn -sV -p 22 --script ssh2-enum-algos,ssh-hostkey,ssh-auth-methods TARGET
```

记录：版本、KEX/cipher、host key、认证方式。

---

## RDP — 3389

```bash
nmap -Pn -sV -p 3389 --script rdp-enum-encryption,rdp-ntlm-info TARGET
```

记录：NLA、TLS、hostname/domain/build hints。

---

## WinRM — 5985/5986

```bash
curl -si http://TARGET:5985/wsman | head -30
openssl s_client -connect TARGET:5986 </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer
```

凭据有效性/执行能力由凭据或攻击阶段判断，不在 Recon 中跑命令。

---

## SNMP — 161/UDP

仅使用已知 community/credential：

```bash
snmpwalk -v2c -c COMMUNITY TARGET 1.3.6.1.2.1.1
snmpwalk -v2c -c COMMUNITY TARGET 1.3.6.1.2.1.2.2.1.2
snmpwalk -v2c -c COMMUNITY TARGET 1.3.6.1.2.1.4.20
```

Windows/Host-Resources MIB 可继续枚举进程/软件，但注意数据量。

---

## rsync — 873

```bash
rsync --list-only rsync://TARGET/
rsync --list-only rsync://TARGET/MODULE/
```

Recon 只列 module/ACL，不默认递归下载或写入。

---

## VNC — 5900+

```bash
nmap -Pn -sV -p 5900 --script vnc-info TARGET
```

记录 auth/security types；密码爆破不在 Recon。

---

## LDAP — 389/636（通用）

```bash
ldapsearch -x -H ldap://TARGET -s base -b '' namingContexts supportedLDAPVersion supportedSASLMechanisms
openssl s_client -connect TARGET:636 </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer
```

匿名 search 只在 rootDSE 指示允许时继续。

---

## TFTP — 69/UDP

```bash
nmap -Pn -sU -p 69 -sV TARGET
```

TFTP 无目录列表；只有已知文件名才做只读 GET 验证，禁止盲目字典下载。
