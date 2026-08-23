# Network / Embedded Devices — Printer / NAS / BMC / Router / Camera / Appliance

Recon 只负责把设备**识别到足以选择攻击链**。不因为目标是打印机/防火墙/NAS 就降低信息深度。

---

## 1. 常见端口指纹

```text
Printer/MFP: 80/443, 161/udp, 515, 631, 9100, 445
NAS:         80/443, 445, 111/2049, 873, 22
BMC:         443, 623/udp, 5900, 17990, Redfish HTTPS
Router/SW:   22/23, 80/443, 161/udp, 500/4500, vendor-specific
Firewall:    80/443, 500/4500 UDP, DNS proxy/server, vendor management
Camera/NVR:  80/443, 554 RTSP, 8000/vendor, 3702 WS-Discovery
VoIP/PBX:    5060/5061 SIP, 80/443 management
Virtualization/LB: 443, vendor APIs, syslog/control-plane services
```

输出必须尽量包含：

```text
vendor
exact product/model
firmware/software build
hardware generation if relevant
management protocol
feature exposure
current/anonymous auth state
```

---

## 2. SNMP 设备识别

已知 community：

```bash
snmpwalk -v2c -c COMMUNITY TARGET 1.3.6.1.2.1.1
snmpwalk -v2c -c COMMUNITY TARGET 1.3.6.1.2.1.2.2.1.2
snmpwalk -v2c -c COMMUNITY TARGET 1.3.6.1.2.1.43
```

记录：

```text
sysDescr / sysObjectID
vendor/model
serial
hostname
firmware
interfaces
location/contact
Printer-MIB identity
```

对 Epson 等设备，**serial/SNMP exposure 本身可能成为后续 credential chain 的前置证据**，因此不要只记录“SNMP readable”。

---

## 3. Printer / MFP

### IPP — 631

```bash
nmap -Pn -sV -p 631 --script cups-info TARGET
ipptool -tv ipp://TARGET/ipp/print get-printer-attributes.test 2>/dev/null | head -160
```

重点记录：

```text
printer-make-and-model
printer-firmware-name/version
printer-uri-supported
document-format-supported
IPP version
PostScript/PCL/PDF capabilities
```

### JetDirect / RAW — 9100

```bash
printf '\033%%-12345X@PJL\r\n@PJL INFO ID\r\n@PJL INFO CONFIG\r\n@PJL INFO FILESYS\r\n\033%%-12345X' | nc -w 5 TARGET 9100
```

记录：

```text
PJL response
PostScript/PCL support
filesystem capability candidate
management auth
LDAP/SMB/SMTP/FTP integration clues
```

### PRET Recon mode

```bash
./pret.py -s TARGET pjl
./pret.py -s TARGET ps
./pret.py -s TARGET pcl
```

在 `/recon` 只确认语言/feature；filesystem write/job manipulation/device-state 操作留 `/service-attack`。

### 现代 CVE candidate

至少检查：

```text
Epson CVE-2025-35970 prerequisite
Epson CVE-2025-66635 model/firmware
HP HPSBPI04007 / CVE-2025-26506 family
Lexmark EWS/PJL/PostScript/IPP advisories
```

不要只输出 CVE；必须写 affected/fixed version confidence。

---

## 4. BMC / IPMI / Redfish

```bash
sudo nmap -Pn -sU -p 623 --script ipmi-version TARGET
curl -sk https://TARGET/redfish/v1/ | jq 2>/dev/null
```

记录：

```text
vendor / iLO / iDRAC generation
firmware exact version
IPMI version
Redfish service
RAKP hash exposure candidate
Cipher 0 candidate (separate check)
current auth level
```

2026 Dell iDRAC CVE 需要 firmware + privilege + network-position gate，不要只按“iDRAC9”匹配。

---

## 5. NAS / Storage Appliance

```bash
nmap -Pn -sV -p 22,80,443,445,111,873,2049 TARGET
smbclient -L //TARGET/ -N
showmount -e TARGET
rsync --list-only rsync://TARGET/
```

记录：

```text
QNAP/Synology/Dell/etc product
QTS/QuTS/DSM/Data Domain version
File Station / app version
web/API auth state
SSH/file services
backup/snapshot/cloud-sync exposure
```

QNAP 2026 advisories必须精确到产品/应用版本。

---

## 6. Firewall / Router / Switch / Load Balancer

```bash
nmap -Pn -sV -p 22,23,53,80,443 TARGET
sudo nmap -Pn -sU -sV -p 53,161,500,4500 TARGET
```

记录：

```text
PAN-OS / FortiOS / ASA / IOS-XE / Junos / QuNetSwitch / Avi etc.
exact build
management interface
IKEv2
Captive Portal/User-ID Portal
DNS Proxy / DNS Server
SNMP
control-plane feature exposure
```

2026 高价值候选包括：

```text
PAN-OS CVE-2026-0300
PAN-OS CVE-2026-0263
PAN-OS CVE-2026-0264
QNAP QuNetSwitch QSA-26-11
VMware Avi VMSA-2026-0005.1
```

Recon 输出 candidate + prerequisite；利用留 `/service-attack`。

---

## 7. Virtualization / Management Appliance

发现 vCenter/Avi/其他管理平面时记录：

```text
product
exact build
control-plane endpoints
syslog / management service exposure
current auth state
```

vCenter 2026 CVE-2026-59310 应比较 Broadcom VMSA-2026-0006 fixed build；不要使用模糊“vCenter 8 vulnerable”说法。

---

## 8. Camera / NVR / RTSP

```bash
nmap -Pn -sV -p 80,443,554,8000 TARGET
ffprobe -v error rtsp://TARGET/ 2>&1 | head
```

记录：vendor/model/firmware、anonymous RTSP、ONVIF/vendor API、management auth、NAS/FTP/SMTP/cloud integration clues。

---

## 9. 输出模板

```text
Device class:
Vendor/Product/Model:
Firmware/Build:

Reachable management/protocols:
...

Authentication state:
...

Feature exposure:
...

Known relationships:
...

High-value candidates:
- CVE / protocol abuse / credential chain
- prerequisite still missing
- affected/fixed version confidence
```
