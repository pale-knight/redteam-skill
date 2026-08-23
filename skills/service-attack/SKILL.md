---
name: service-attack
description: "直连网络服务攻击链。用于已经识别/枚举的非专门领域服务，从数据库、数据存储、文件/远程访问、基础设施、消息队列、DNS/网络服务、打印机/MFP/NAS/BMC/网络设备等服务入口继续利用到凭据、代码执行、主机控制、横向能力或新的独立身份。由操作者选择具体攻击链；不自动切换模块。"
---

# /service-attack — 直连服务利用

> **scope：** 已经知道目标服务是什么、版本/认证/权限状态，并由操作者选择“直接攻击这个网络服务”后，完成该服务视角下的连续利用链。
>
> 本模块是**利用模块**，不是 Recon 的第二遍。目标是 credential、server-side execution、**shell**、host/device control。高影响/破坏性原语不删除，标 Impact 和恢复，由操作者决定是否执行——不要畏手畏脚改成只读验证。

工具安装参阅 `../shared/tools.md`。CVE 有精确版本才 `../shared/cve-enrichment.md`。禁止开局把下面配方全读：先看端口/协议，再 Read **一份**（§3–5）。设备固件门控：走到 CVE 时才 `references/vulnerability-intelligence.md`。

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

## 0. 工作方式

每条攻击链按你的半自动模式写：

```text
Current evidence
→ prerequisites / exact version / current privilege
→ operator-selected primitive
→ exploit / configuration abuse / protocol abuse
→ privilege / relationship expansion
→ credential / execution / host-device control result
→ restore / cleanup when state was changed
```

**禁止从产品名直接跳到 exploit。** 必须先验证：

```text
version / firmware
platform/OS/architecture
current identity
current privilege
feature/module/config
network reachability
public PoC/tool compatibility when CVE-dependent
```

### Impact 标签

```text
READ        数据/配置/文件读取
WRITE       文件/对象/配置写入
CONTROL     服务/设备/作业/账户控制
EXECUTION   服务端命令/代码执行
HOST        主机/节点/设备操作系统控制
DESTRUCTIVE 格式化、擦除、恢复出厂、断电、批量业务破坏等
```

`DESTRUCTIVE` **不是禁止项**。它必须写清：前置条件、预期影响、是否可恢复，并等待操作者明确选择。

---

## 0.4 自动漏洞库 / CVE Candidate Enrichment

从 `/recon` 接到 `product/version/firmware/CPE` 后，真正 exploit 前再按 `../shared/cve-enrichment.md` 做一次：

```text
exact version/firmware
→ cvemap/vulnx
→ KEV/EPSS
→ PoC/Nuclei
→ vendor fixed-version gate
→ protocol/feature/auth prerequisite
```

```bash
cvemap -p '<product>' -s critical,high -f age,kev,epss,poc,template
cvemap -id CVE-YYYY-NNNN -j
```

Scanner banner/CVE hit 不算成功；operator 已选 direct-service 路径后，本模块继续走到真正 execution/shell/control。

---

## 0.5 Endpoint Defense Boundary — 可选 /edr-bypass Handoff

`/service-attack` 自己负责 service auth/config/protocol/CVE primitive 到 execution/shell/control。

```text
service ACL/auth/config blocks primitive
→ 留 /service-attack

service-side command execution 已确认
+ 当前 payload 被 host endpoint AV/EDR/AMSI/application-control 阻断
→ operator may select /edr-bypass
→ 解决后返回 /service-attack
→ 完成当前 direct-service chain
```

例如：

```text
MSSQL xp_cmdshell disabled      → Service
xp_cmdshell permission denied   → Service
xp_cmdshell 'whoami' 成功，但 payload.exe 被 Defender 杀 → EDR handoff
```

---

## 1. 成功条件

满足任一：

```text
server-side command/code execution
interactive/remote shell
new reusable credential/hash/token
control of another linked service/server
write primitive with demonstrated execution/security impact
service-admin / infrastructure-admin / device-admin capability
host/device control
new independent cloud/domain/K8s/CI identity obtained through this chain
```

仅“读到 banner / scanner 报 CVE / PoC 看起来匹配”不算成功。

---

## 2. 状态修改与恢复

对可回滚改动：

```text
snapshot original value
→ execute selected primitive
→ verify result
→ restore original value
```

对不可逆/高影响行为：

```text
mark Impact=DESTRUCTIVE
→ state exact effect
→ state recovery possibility
→ wait for operator selection
```

不要因为操作高影响就从 Skill 中删掉该技术；也不要把高影响技术混成默认第一步。

---

## 3. 数据库家族

```text
1433 MSSQL      → references/database-mssql.md
3306 MySQL      → references/database-mysql.md
5432 PostgreSQL → references/database-postgresql.md
1521 Oracle     → references/database-oracle.md
6379 Redis etc. → references/datastore-nosql.md
```

入口是数据库/数据服务本身，因此可以把数据库视角的 direct-service chain 走到 shell/credential/linked-system control。

---

## 4. 文件 / Remote Services

```text
NFS / SMB / FTP / rsync / TFTP → references/file-services.md
SSH / RDP / WinRM / VNC        → references/remote-access.md
```

如果服务链自然得到 shell，就在“稳定 host access”处闭环。之后是否继续 OS 提权由操作者决定；不要为了模块纯净在 shell 之前人为截断。

---

## 5. Infrastructure / Message / Device

```text
Docker / Vault / Consul / Nomad / etcd     → references/infrastructure.md
RabbitMQ / Kafka / MQTT / ActiveMQ / NATS → references/messaging.md
DNS / SNMP / IPMI                         → references/dns-network-services.md
Printer / MFP / NAS / BMC / Appliance     → references/network-devices.md
设备/管理面 CVE                           → 先版本门控 references/network-appliance-cves.md
```

对设备类目标的目标优先级：

```text
credential / trust relationship
→ admin/control plane
→ code execution / host-device control
→ lateral/pivot capability
→ persistence/config control
→ destructive capability（operator-selected）
```

---

## 6. CVE 链要求

现代网络设备和 appliance 固件碎片化严重。CVE 链必须包含：

```text
vendor + exact model/product
+ exact firmware/software branch
+ required feature/service
+ auth level / network position
+ fixed-version comparison
+ reliable public PoC/tool status
```

如果只有 vendor advisory、没有公开稳定 PoC：

```text
标记 REAL / VERSION-GATED / NO-STABLE-PUBLIC-POC
```

保留为真实候选，但**不生成虚假的 exploit command**。

## 完成后

写入 `./notes.md`。候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。
