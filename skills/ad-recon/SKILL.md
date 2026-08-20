---
name: ad-recon
description: "Active Directory reconnaissance with or without credentials: user/group/computer enumeration, ACL/delegation, ADCS, modern Windows LAPS, BloodHound, Server 2025/dMSA/Ghost SPN candidates, and trust mapping. Recon only — do not exploit Kerberoast-to-DA, DCSync, or change passwords. Operator may select /ad-attack after cards are ready."
---

# /ad-recon — 域信息收集

> **scope：** 把域打成 **路径/ACL/证书/LAPS/委派卡片**。只读（含用已知凭据的 LDAP）。不 DCSync、不改密、不 RBCD。▸ 操作者选 `/ad-attack` 再打。现代 LAPS 读取（有权限时）算 recon 的凭据发现，打域仍交 attack。

工具：`../shared/tools.md`。CVE：有 DC 精确 build 才 Read `../shared/cve-enrichment.md`（禁止 Windows 2025 dump 全部 CVE）。

走到才 Read（一次一份）：

- 精确 LDAP / nxc 命令习惯 → `references/ad-enum-cheatsheet.md`
- LAPS 全属性 → `references/windows-laps.md`
- BloodHound 查询 → `references/bloodhound-queries.md`
- 老环境 PowerView → `references/powerview-cheatsheet.md`
- 2025/dMSA/Ghost SPN 情报门控 → `references/vulnerability-intelligence.md`

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

## 0. 成功条件

```text
域 / DC / 功能级别 / 是否 2025
当前身份与权限
用户/组/计算机/ACL/委派/ADCS/LAPS 可读性
BloodHound 路径候选
2025/dMSA/Ghost SPN/WAC 卡片（门控 UNKNOWN 就标 UNKNOWN）
```

**禁止：** 利用 ESC、重置密码、PTH 打 DA、把「有 SPN」写成「已 Kerberoast 成功」。

---

## 1. 决策树

```text
无凭据     → kerbrute；详细匿名 LDAP → Read references/ad-enum-cheatsheet.md
有域用户   → nxc + bloodyAD（选一条主工具做完）→ 命令对照 Read references/ad-enum-cheatsheet.md
只要 ACL   → bloodyAD 可写对象
只要委派   → findDelegation
只要证书   → certipy find
只要 LAPS  → Read references/windows-laps.md（只读，不横移）
2025 DC    → 情报门控 Read references/vulnerability-intelligence.md
图         → BloodHound CE → 查询 Read references/bloodhound-queries.md
老 PowerView → 仅当 BH 不可用，Read references/powerview-cheatsheet.md
要隐蔽     → SOAPHound / ADExplorer 离线
```

不要 kerbrute + nxc + ldapsearch + bloodyAD 无脑全跑。

---

## 2. 无凭据

```bash
kerbrute userenum -d corp.com --dc DC users.txt
# LDAP 匿名、rpcclient、smb 空会话：失败就停，改有凭据
```

详细命令习惯仍在操作者常用 nxc 匿名模块；本 SKILL 不贴全书。

---

## 3. 有凭据（一条主路径）

首选 nxc + 需要 ACL 时 bloodyAD：

```bash
nxc smb DC -u jen -p 'pass'
nxc ldap DC -u jen -p 'pass' --users --groups --computers
```

SPN / 委派 / 描述字段里的口令 → **记卡片**（有 SPN、etype 线索、明文备注）。不要在 recon 里 GetUserSPNs，也不要预支「破解交 `/creds`」。操作者若选 `/ad-attack`，由 attack **要票+当场砸+接着用**。

精确 LDAP / GPP / SYSVOL → 保持用现有命令；GPP `cpassword` 解出的口令当凭据候选。

LAPS（legacy + Windows LAPS 全属性）→ **`references/windows-laps.md`**。读到的口令写进卡片，**recon 不横移**。下一步由操作者选 `/ad-attack` 或 `/creds`（当独立凭据作业），不要在这里 PsExec。

---

## 4. 2025 / ADCS / 图

DC 版本、etype、dMSA OU、ResetNightmare 可写 UPN、Ghost SPN、WAC 端口：记 **候选 + 补丁未知**，不要当已确认洞。CVE 走 enrichment。

ADCS：`certipy find -vulnerable` → 模板/CA/EKU 卡片交 `/ad-attack`。

BloodHound CE 采集与 OpenGraph 备注保持现有流程（SharpHound 有 EDR 风险，标一下）。分析是 recon；沿最短路径打是 attack。

信任：`nltest` / bloodyAD，只判断方向。

隐蔽：SOAPHound、ADExplorerSnapshot。

---

## 5. 输出

```text
[AD-RECON]
identity / DC build:
paths: Kerberoast? ACL? ADCS ESC#? dMSA? LAPS readable?
next: waiting operator（候选只认 ~/.claude/skills/shared/modules.yaml）
```
