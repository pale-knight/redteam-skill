# Network / Management Appliance — 2025–2026 High-Value CVE Candidates

> 这些条目用于现实红队/靶场中的**高价值候选链**。必须 exact-version / feature / auth / network-position gate。没有公开稳定 PoC 时，不虚构 payload。

---

## 1. Palo Alto PAN-OS — 2026

### CVE-2026-0300 — Captive Portal unauthenticated root RCE

**REAL / VENDOR-CONFIRMED / UNAUTHENTICATED / FEATURE-GATED**

Palo Alto 官方描述：User-ID Authentication Portal / Captive Portal 的 buffer overflow 可让未认证攻击者以 root 权限执行任意代码。

Gate：

```text
PAN-OS exact version
+ affected release branch
+ Captive Portal/User-ID Authentication Portal relevant service reachable/enabled
+ not on fixed version
```

链：

```text
network access
→ vulnerable portal service
→ reliable PoC/tool compatibility
→ root command/code execution
```

无兼容公开 PoC时：保留为优先 CVE candidate，不生成猜测 payload。

### CVE-2026-0263 — IKEv2 RCE

**REAL / VENDOR-CONFIRMED / NETWORK / FEATURE-GATED**

Palo Alto 官方列为 IKEv2 processing Remote Code Execution。

```text
UDP/500 or 4500 / IKEv2 exposure
+ affected PAN-OS branch
→ exact version gate
→ reliable PoC
→ RCE
```

### CVE-2026-0264 — DNS Proxy / DNS Server unauthenticated RCE

**REAL / VENDOR-CONFIRMED / UNAUTHENTICATED / FEATURE-GATED**

```text
PAN-OS DNS Proxy/DNS Server feature reachable
+ affected version
→ heap overflow candidate
→ RCE if compatible exploit exists
```

---

## 2. VMware vCenter — CVE-2026-59310

**REAL / VENDOR-CONFIRMED / CRITICAL / NETWORK-RCE**

Broadcom VMSA-2026-0006：vCenter Syslog server directory traversal，网络可达攻击者可能利用并执行任意代码。

Fixed branches include vendor-listed patched versions such as vCenter 8.0 U3k / U2f and corresponding 9.x fixes;以当前 advisory response matrix 为准。

链：

```text
vCenter identified
→ exact 8.x/9.x build
→ compare VMSA-2026-0006 fixed version
→ vulnerable Syslog server path reachable
→ public reliable PoC/exploit compatibility
→ arbitrary code execution
```

此项应给高优先级，因为是**管理平面网络 RCE**，成功后影响虚拟化基础设施，而不是普通单主机 Web RCE。

---

## 3. VMware Avi Load Balancer — VMSA-2026-0005.1

### CVE-2026-47865 — Authentication Bypass
### CVE-2026-47867 — Remote Code Execution
### CVE-2026-47869 / 47870 — Authenticated RCE / Privilege Escalation

**REAL / VENDOR-CONFIRMED / VERSION-GATED**

Broadcom 官方披露 Avi Load Balancer 22.x/30.x 等受影响版本存在 authentication bypass、authorization bypass 和多个 RCE/privilege escalation 问题。

重点链：

```text
Avi Control Plane reachable
→ exact version
→ auth bypass applicability
→ control-plane access
→ RCE candidate
→ appliance/root control
```

不要把多个 CVE 自动串成一条链；必须分别验证受影响版本、auth requirement 和 PoC compatibility。

---

## 4. QNAP QuNetSwitch — QSA-26-11

**REAL / VENDOR-CONFIRMED / CRITICAL**

QNAP 2026 advisory 对 QuNetSwitch 2.0.x 披露：

```text
CVE-2026-22897 remote command injection
CVE-2026-22900 hard-coded credentials → unauthorized access
CVE-2026-22901 authenticated command injection
CVE-2026-22902 admin/local command injection
```

Fixed version以 QSA-26-11 为准。

链候选：

```text
QuNetSwitch exact version
├─ hard-coded credential condition → unauthorized access
└─ command injection condition     → OS command execution
```

若目标已是 fixed build，不继续执行旧 PoC。

---

## 5. QNAP QTS / QuTS / QVP — QSA-26-10

**REAL / VENDOR-CONFIRMED / AUTH-GATED**

2026 advisory 包含多个 command injection、path traversal、access-control 问题。高价值 execution candidates 包括：

```text
CVE-2025-66273 authenticated-admin command injection
CVE-2025-66279 authenticated-admin command injection
CVE-2026-22893 authenticated-admin elevated command injection
CVE-2026-24719 authenticated-admin command injection
```

使用方式：

```text
QTS/QuTS exact version
+ current role/admin level
→ select matching CVE
→ compare fixed version
→ reliable PoC
→ NAS OS command execution
```

不要因已有 admin 就忽略这些链：NAS 管理员权限和 NAS OS command execution 不是同一个能力。

---

## 6. Dell iDRAC9 / iDRAC10 — 2026

### CVE-2026-26945 — Process Control → Code Execution

**REAL / VENDOR-CONFIRMED / HIGH-PRIVILEGE + ADJACENT-NETWORK GATED**

Dell 2026 advisory：部分 iDRAC9 / iDRAC10 版本存在 Process Control vulnerability；高权限且 adjacent-network 的攻击者可能利用导致 code execution。

链：

```text
iDRAC admin/high privilege
+ adjacent network condition
+ affected firmware
→ CVE-2026-26945 candidate
→ code execution
```

这是典型**BMC admin → deeper code execution**链，不是未认证 RCE。

---

## 7. Dell PowerProtect Data Domain — 2026

Dell DSA-2026-278 对 Data Domain 多个版本披露多个 command injection / path traversal / SSRF / authorization issues，其中多个高权限远程 command injection 可导致任意 OS 命令执行。

高价值候选包括：

```text
CVE-2026-49815
CVE-2026-26355
CVE-2026-53478
CVE-2026-49814
```

Gate：

```text
Data Domain exact branch/build
+ required privilege level
+ remote management reachability
→ vendor fixed version comparison
→ reliable PoC
→ OS command execution
```

---

## 8. Selection Rule

优先排序：

```text
unauthenticated network RCE
> auth bypass → admin/control
> low-priv → RCE
> admin → OS/RCE
> file read/write / SSRF / DoS
```

但真正是否执行取决于：

```text
exact match
public exploit maturity
current objective
operator selection
```
