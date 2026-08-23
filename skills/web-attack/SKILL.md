---
name: web-attack
description: "HTTP/Web exploitation until a server shell or equivalent OS execution. Use after /web-recon has mapped the application. Covers injection, upload, LFI, SSRF/XXE, SSTI, deserialization, JWT/SAML, API logic, desync/cache/parser, and Web-controlled backend abuse. WAF stays here. Endpoint blocks after OS execution hand off to /edr-bypass then return. Direct non-HTTP service ports belong to /recon or /service-attack."
---

# /web-attack — Web 漏洞利用

> **scope：** 从 HTTP/Web 输入把当前链打到 **服务器 Shell**（或等价 OS 执行）。直连 1433/3306/6379 不是这里。WAF/上传过滤留本模块。▸ Shell 一旦拿到，记 notes；候选只认 `~/.claude/skills/shared/modules.yaml`（`modules.py tail`）。

工具：`../shared/tools.md`。产品 CVE 由 `/web-recon` 出；利用仍在本模块打到 shell。有精确版本才读 `../shared/cve-enrichment.md`。

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
Web 输入 / 功能 / API
        ↓
漏洞成立
        ↓
命令执行 / 可执行文件落地 / 管理身份 + 执行点
        ↓
服务器 Shell？
├─ NO  → 继续当前 Web 链（SQLi→OS、XSS→后台→上传、SSRF→Redis）
└─ YES → /web-attack COMPLETE
```

**不算：** sqlmap 报 injection、`alert(1)`、能传 jpg、Nuclei MATCH。

---

## 0.4 不要吸收

| 东西 | 去哪 |
|---|---|
| 直连数据库/Redis 端口 | `/recon` `/service-attack` |
| 路径枚举 / 指纹 / 已知 CVE 发现 | `/web-recon` |
| 本机提权 | `/privesc-*` |
| JWT 弱密钥短字典 | **本模块** `jwt_tool -C`，爆了立刻签发继续打 shell |
| JWT 长时间 GPU / 全 rockyou | 仅操作者另开凭据作业 → 候选 `/creds` |

---

## 0.5 EDR

WAF / 上传过滤 / parser / cache = **本模块**。  
OS 上执行被 AV 杀 → `/edr-bypass` → 回本模块拿完 shell。

---

## 1. 决策树（按手上是什么，只读一份）

```text
HTTP 参数像注入
  → SQLi：先 Read references/sqli.md 指纹 DBMS
     再只读 sqli-mssql|mysql|postgresql|oracle-chain.md 之一
  → CMDi：Read references/cmdi.md
  → SSTI：Read references/ssti.md
  → NoSQL/ORM：Read references/auth-bypass.md 或 references/orm-leak.md
文件 / 包含 / 上传
  → 上传：Read references/upload.md（先问栈，不要默认 PHP）
  → 包含：Read references/lfi-rfi.md
服务端出站
  → XXE：Read references/xxe.md ；SSRF：Read references/ssrf.md ；Rogue MySQL：Read references/server-side-client-abuse.md
Token / SAML / JWT
  → JWT：Read references/jwt.md ；SAML：Read references/saml-security.md
序列化
  → PHP/.NET/pickle：Read references/deserialization.md
  → Java/Fastjson：Read references/java-deserialization.md
代理/CDN（recon 已确认才走）
  → desync / cache / parser / waf-bypass 各读当前那一份
API 逻辑
  → Read references/api-security.md ；XSS 接执行 Read references/xss.md
```

同一条链打穿再换。不要按课表把上表全跑一遍。

---

## 2. 注入类

```bash
sqlmap -r request.txt -p param --current-user --current-db --privileges --batch
```

确认 DBMS 后再 Read 对应 `references/sqli-*-chain.md`。不要一上来 `--os-shell`。

---

## 3. 文件 / 包含 / 上传

**上传** → 现在 Read `references/upload.md`：定位 URL + 解释器执行 = getshell。IIS / Tomcat / Node，禁止默认 `.phtml`。

**LFI** → 现在 Read `references/lfi-rfi.md`。能 include 才走 filter chain。

---

## 4. 出站

XXE / SSRF 分别 Read。SSRF 拿到云密钥、Web 再走不动 → 候选 `/cloud-recon`。还能 gopher/Redis 拿 shell 就先打完 Web。

---

## 5. JWT / SAML

弱密钥 **本模块砸**：

```bash
jwt_tool <token> -C -d /usr/share/wordlists/rockyou.txt
hashcat -m 16500 jwt.txt wordlist.txt
jwt_tool <token> -S hs256 -p '<密钥>' -T
```

完整算法绕过现在 Read `references/jwt.md`。SAML 现在 Read `references/saml-security.md`。

---

## 6. 反序列化

头：PHP `O:`、Java `rO0AB`、.NET `AAEAAAD`、pickle `\x80`。按栈只读一份。

---

## 7. API / XSS

越权不是终点，接到执行。现在 Read `references/api-security.md` 或 `references/xss.md`。

---

## 8. 代理边界

仅 recon 已确认 CDN/反代时，才 Read desync/cache/parser/waf 中**当前那一种**。

---

## 9. 完成后

```text
shell: host / user / 怎么拿到的
RESTORE: 删的马 / 还原的 web.config
```

写入 `./notes.md`（shell 用户/路径/RESTORE）。候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。
