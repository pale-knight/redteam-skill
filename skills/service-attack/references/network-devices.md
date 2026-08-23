# Network / Embedded Devices Attack Chains

覆盖：Printer/MFP、NAS、BMC/iLO/iDRAC、Router/Switch、Firewall、Camera/NVR、IT appliance。OT/ICS 不在本 reference。

> 这是利用 reference。`/recon` 已经完成 vendor/model/firmware/protocol 识别；这里从操作者选中的设备攻击面继续做到控制、凭据、执行、主机/设备控制或高影响 primitive。

---

# 1. Printer / MFP — 协议原生攻击

## 1.1 Gate

```text
9100 / 515 / 631 / vendor management reachable
vendor + model + firmware known
printer language / IPP capabilities known
management/auth state known
```

常见攻击面：

```text
PJL
PostScript
PCL
ESC/POS
IPP
RAW/JetDirect 9100
Embedded Web Server
SNMP
SMB/LDAP/SMTP/FTP/SFTP integration
local spool/storage
```

---

## 1.2 PRET — PJL / PostScript / PCL

PRET 是经典 Printer Exploitation Toolkit。项目较老、Python2，但它实现的 PJL/PostScript/PCL filesystem/job/config/device primitives 仍然是现实打印设备协议攻击面。

```bash
./pret.py TARGET pjl
./pret.py TARGET ps
./pret.py TARGET pcl
```

进入交互后先确认实现支持的命令：

```text
help
id
info id
info config
info filesys
pwd
ls
```

### Filesystem primitive — READ / WRITE

如果设备实现允许：

```text
ls <path>
cat <path>
get <remote> <local>
put <local> <remote>
delete <remote>
```

攻击目标不是“能 ls”本身，而是继续判断：

```text
configuration / address book
scan destinations
stored integration data
spool/job data
credential material
writable configuration/startup objects
```

若 `put` 可写到会被设备解释/加载的对象，继续验证其真实安全影响。

### Job primitive — CONTROL

根据 printer language / firmware 支持，PRET 可用于：

```text
capture / inspect jobs
manipulate print jobs
modify printer-side state
```

成功判据是**真实 job/control capability**，不是单纯 TCP/9100 可连接。

### High-impact primitives — DESTRUCTIVE

PRET 项目本身包含可能造成物理/持久状态影响的能力，例如 reset / format / destructive printer-language operations。

这些能力保留在攻击知识中，但执行前必须输出：

```text
Impact: DESTRUCTIVE
Target: exact device
Primitive: reset / format / erase / state damage
Expected outage/data loss: ...
Recovery: known / unknown / factory intervention
```

然后等待操作者选择。

**不要把“高影响”误写成“技术不存在”。**

---

## 1.3 RAW 9100 / PJL 直接协议

没有 PRET 兼容环境时，可直接使用 PJL/UEL 做 protocol-native 操作。首先确认语言和响应：

```bash
printf '\033%%-12345X@PJL\r\n@PJL INFO ID\r\n@PJL INFO CONFIG\r\n\033%%-12345X' | nc -w 5 TARGET 9100
```

如果设备返回 PJL filesystem/config capability，继续使用**该厂商实际支持**的 PJL FS 命令；不要假设所有打印机支持同一文件系统语义。

---

# 2. Epson 现实攻击链

## 2.1 CVE-2025-35970 — SNMP → 初始 WebConfig 管理员密码

**REAL / VENDOR-CONFIRMED / MODEL-GATED**

Epson 官方披露：部分产品的初始 WebConfig 管理员密码与序列号相关，而序列号可通过远程 SNMP 获取；如果初始管理员密码没有被修改，远程攻击者可能获得 WebConfig 管理权限。

链：

```text
Epson device
→ affected model/firmware
→ SNMP reachable
→ obtain serial/device information
→ derive/check initial admin credential per affected product behavior
→ WebConfig administrator access
```

成功判据：

```text
WebConfig administrator session established
```

不要把“能读 SNMP serial”直接写成“admin compromise”；必须验证管理员密码仍保持初始状态。

## 2.2 CVE-2025-66635 — WebConfig Admin → Command Execution

**REAL / VENDOR-CONFIRMED / AUTH-REQUIRED / MODEL-GATED**

Epson 官方把该问题定义为 WebConfig command execution vulnerability。只有当前产品/版本同时满足 advisory 条件且已经获得管理员凭据时才进入。

链：

```text
WebConfig admin
→ exact affected model/firmware
→ CVE-2025-66635 prerequisite satisfied
→ reliable public PoC/tool available?
   ├─ YES → operator-selected command marker → execution result
   └─ NO  → mark NO-STABLE-PUBLIC-POC; do not fabricate payload
```

如果与 CVE-2025-35970 条件重叠，可形成：

```text
SNMP
→ initial credential
→ WebConfig admin
→ command execution candidate
```

## 2.3 Epson POS TCP/9100 / ESC-POS

部分网络 POS printer 的 raw printing service 本身没有预定义的认证/加密，网络可达者可发送 ESC/POS printer commands。

```text
Impact: CONTROL
```

这代表**设备命令语言控制**，不是自动等价 OS shell。根据型号支持的 ESC/POS 功能评估真实设备动作。

---

# 3. HP LaserJet — PostScript / Print-job RCE Candidate

## CVE-2025-26506 / HPSBPI04007 family

**REAL / VENDOR-CONFIRMED / MODEL+FIRMWARE-GATED**

HP 官方安全公告 HPSBPI04007 对部分 LaserJet Pro / Enterprise / Managed 设备披露潜在 Remote Code Execution / Privilege Escalation，包含 CVE-2025-26506 等。

流程：

```text
HP LaserJet identified
→ exact product number / firmware
→ PostScript / relevant print path reachable
→ compare HPSBPI04007 affected/fixed table
→ public reliable exploit/PoC status
→ operator-selected execution marker if compatible
```

没有匹配 product/firmware 时不要根据“HP + 9100”盲打。

---

# 4. Lexmark — PJL / PostScript / IPP / EWS

Lexmark 官方历史/当前 advisory 明确覆盖过：

```text
PJL directory traversal / overwrite
PostScript buffer/memory corruption
IPP buffer overflow
Embedded Web Server RCE/command injection
SNMP input validation
firmware downgrade / persistence-related weaknesses
```

策略：

```text
model + firmware
→ identify attack surface (PJL/PS/IPP/EWS/SNMP)
→ exact advisory/fixed version
→ reliable exploit
→ selected primitive
```

Lexmark 设备不要只按 PRET；现代 firmware CVE 和 EWS/API 链应优先做精确版本匹配。

---

# 5. Printer / MFP Credential & Infrastructure Pivot

获得 printer/MFP admin 或 filesystem/config read 后，继续枚举：

```text
scan-to-SMB
LDAP directory integration
SMTP relay/auth
FTP/SFTP destination
address book
fleet/print management server
SMB share / file server hostname
service account username
certificate/private key material
```

攻击链目标：

```text
device control
→ stored/reusable credential or trust relationship
→ validate credential against its actual service
→ new identity / linked infrastructure control
```

如果凭据是可复用明文/token/key，成功条件应记录作用域和真实认证结果。

---

# 6. IPP / CUPS / Print Infrastructure

打印机本身也可能成为客户端/print server 的输入源。

经典现代案例：OpenPrinting cups-browsed / IPP attribute chain（CVE-2024-47176 family）展示了：

```text
attacker-controlled / malicious IPP printer data
→ vulnerable print discovery / PPD generation
→ client/server-side command execution condition
```

因此发现 CUPS/IPP infrastructure 时，不只看 printer device：

```text
printer
↔ IPP
↔ CUPS / print server / fleet manager
```

按目标系统的 CUPS/cups-browsed/libcupsfilters/libppd 版本和实际服务暴露判断，不把 2024 链写成现代 Linux 通杀。

---

# 7. NAS

NAS 是完整服务器/存储 appliance，不应只做到 share listing。

攻击面：

```text
SMB/NFS/rsync
vendor Web/API
SSH
package/app services
snapshot/backup
cloud sync
stored credentials
container/VM service
```

成功目标：

```text
admin/session
→ command execution
→ NAS OS shell
→ data / credential / backup control
```

QNAP 2026 现实 CVE 见 `network-appliance-cves.md`。

---

# 8. BMC / iLO / iDRAC / Redfish

## 8.1 已获 BMC Admin

```bash
curl -sk -u USER:PASS https://TARGET/redfish/v1/Systems/ | jq
curl -sk -u USER:PASS https://TARGET/redfish/v1/Managers/ | jq
```

BMC admin 的真实高价值能力包括：

```text
remote console
virtual media
boot override
firmware/config
power control
hardware inventory
host lifecycle control
```

其中：

```text
remote console / virtual media / boot control → CONTROL/HOST
power off/reset                     → DESTRUCTIVE/HIGH IMPACT
```

不要把 Power/VirtualMedia 从模块里删掉；执行前标明会不会中断目标业务。

## 8.2 IPMI RAKP

RAKP hash exposure 用于 credential chain：

```text
valid username
→ RAKP HMAC material
→ offline crack
→ BMC credential
→ BMC control plane
→ console/virtual media/host control
```

它与 Cipher 0 是不同 primitive。

Dell iDRAC 2026 version-gated CVE 见 `network-appliance-cves.md`。

---

# 9. Router / Switch / Firewall

获得管理权限后，不要停在 `show version`。

高价值链：

```text
running config
→ local/AAA/SNMP/VPN credentials
→ routing / ACL / NAT / DNS / proxy trust
→ config write
→ traffic/control plane impact
→ credential/pivot/lateral capability
```

可回滚的 config write 使用明确 marker；路由/ACL/VLAN/NAT 等业务影响操作标 `CONTROL/HIGH` 或 `DESTRUCTIVE`，由操作者决定。

2026 PAN-OS、QuNetSwitch 等真实 appliance CVE 见 `network-appliance-cves.md`。

---

# 10. Camera / NVR / VoIP / Other Embedded IT

获得 admin 后继续判断：

```text
media/control plane
stored NAS/FTP/SMTP/cloud credentials
user database
firmware/version RCE
ONVIF/RTSP/vendor protocol
network pivot relationship
```

对摄像机：云台/录制删除/格式化 storage 是高影响能力，不作为“默认 marker”，但保留为操作者可选的设备控制 primitive。

---

# 11. 成功输出模板

```text
Device:
Vendor / Model / Firmware:
Entry primitive:
Current identity:
Impact level:

Confirmed capability:
- READ / WRITE / CONTROL / EXECUTION / HOST / DESTRUCTIVE

Attack chain completed:
...

New credentials / relationships:
...

State changed:
...

Cleanup / restore:
...
```
