# DNS / SNMP / IPMI / Network Services

---

## DNS

### Zone Transfer

```bash
dig @TARGET ZONE AXFR
```

成功即数据泄露/资产扩展，不需要额外破坏性利用。

### Dynamic Update

只有已确认 zone 允许未认证/当前身份 UPDATE 时，用临时记录验证：

```bash
nsupdate
> server TARGET
> zone target.local
> update add sa-marker.target.local. 60 A 192.0.2.123
> send
```

验证后立即：

```text
update delete sa-marker.target.local. A
send
```

生产 DNS 修改会影响解析，必须使用唯一 marker 名称。

---

## SNMP

### Read-write community / SNMPv3 write

先确认：

```bash
snmpget -v2c -c COMMUNITY TARGET 1.3.6.1.2.1.1.5.0
```

如果已知是 RW，**不要盲目 snmpset 常见 OID**。不同设备 OID 的副作用差异巨大；先用 vendor MIB 找可回滚、无业务影响的 test field，再 snapshot→set→verify→restore。

SNMP 的真正红队价值常是：

```text
config / route / interface data
stored credentials on vendor-specific MIB
TFTP config-copy features
network topology
```

这些都需要设备/厂商特定验证。

---

## IPMI / BMC

### RAKP hash exposure

IPMI 2.0 RAKP handshake 对有效用户名可能提供可离线验证的 HMAC 材料；这和 Cipher 0 是两件不同事情。Metasploit `ipmi_dumphashes` 可用于授权 credential audit：

```text
auxiliary/scanner/ipmi/ipmi_dumphashes
```

拿到 hash 后记录并交给离线凭据审计；不要把 hash exposure 直接算主机控制。

### Known credential

```bash
ipmitool -I lanplus -H TARGET -U USER -P PASS user list
ipmitool -I lanplus -H TARGET -U USER -P PASS mc info
```

电源控制/virtual media 属高影响操作，只有靶场明确需要时执行。

---

## SIP / VoIP

```bash
nmap -Pn -sU -p 5060 --script sip-methods TARGET
```

枚举 methods/realm；用户爆破、呼叫泛洪不放本 reference 默认链。
