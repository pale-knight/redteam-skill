---
name: web-recon
description: "HTTP/HTTPS application-layer reconnaissance after a web service is identified: fingerprinting, content/API discovery, JS/source maps, proxy/cache topology, WAF, CMS, and known CVE/PoC candidates. Recon only — do not exploit, write files, or obtain a shell. Hand CVE candidates and attack surface to the operator, who may select /web-attack. Non-HTTP ports belong to /recon."
---

# /web-recon — Web 信息收集

> **scope：** 已发现 HTTP/HTTPS 后，交付技术栈、路径/API、前端线索、代理/缓存边界、已知 CVE **候选**。不手工挖 SQLi、不 exploit、不拿 shell。直连数据库端口 → `/recon`。▸ 候选交操作者选 `/web-attack`。

CVE 统一 `../shared/cve-enrichment.md`。CMS → `references/cms-cheatsheet.md`。深挖：`references/api-discovery.md` / `references/frontend-recon.md` / `references/http-topology.md` / `references/vulnerability-intelligence.md`。

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
技术栈 + WAF 厂商
路径 / API / 方法矩阵
JS / sourcemap / 历史端点
代理/CDN/缓存边界
CVE 候选（版本门 + PoC 有无），不是「已利用」
```

**禁止：** RCE、写文件、爆破登录、改配置、把 Nuclei MATCH 写成已拿下。

---

## 1. 决策树

```text
先指纹（whatweb / 头 / WAF）
        ↓
按栈选字典和扩展名（禁止全局 -e .php）
        ↓
路径 / 参数 / vhost / API / JS
        ↓
有精确产品版本 → ../shared/cve-enrichment.md
        ↓
卡片交给操作者 → 可选 /web-attack
```

IIS → aspx/ashx/config；Tomcat → jsp/war；PHP → php/phtml；未知先无扩展再补。

---

## 2. 指纹

```bash
whatweb http://TARGET
curl -sI http://TARGET
wafw00f http://TARGET
```

记 Server / 语言 / CMS / WAF。WAF 只记厂商，绕过在 `/web-attack`。

---

## 3. 发现（细节在 reference，SKILL 不堆四种工具全书）

路径：ffuf 首选。字典见 `../shared/wordlists.md`。

```bash
# 扩展名跟指纹，不要复制 .php 当全世界
ffuf -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
     -u http://TARGET/FUZZ -mc 200,301,302,403
```

递归 → feroxbuster。参数 → arjun。vhost → Host: FUZZ。完整命令习惯仍可用 ffuf/ferox/gobuster，**选一种做完**，不要四种全跑。

API / Swagger / Kiterunner / GraphQL → **`references/api-discovery.md`**。401/403/405 保留给 attack。

JS / sourcemap / wayback → **`references/frontend-recon.md`**。

`.git` / `.env` / `web.config` 泄露：下载后把密钥 **写进卡片**，recon **不连生产库、不登录**。操作者再选 `/web-attack` 或 `/creds`（当独立凭据作业）。

CMS 识别后 → **`references/cms-cheatsheet.md`**（只扫，不打）。

---

## 4. HTTP 拓扑

进 desync/cache 之前记 CDN/WAF/反代/HTTP 版本 → **`references/http-topology.md`**。

```bash
curl -skI --http1.1 https://TARGET/
curl -skI --http2 https://TARGET/
```

---

## 5. CVE 候选

精确版本后 → **`references/vulnerability-intelligence.md`** + `../shared/cve-enrichment.md`。

```bash
nuclei -u http://TARGET -as -severity critical,high
vulnx search '<product> && is_poc:true' --limit 20
```

Nuclei/PoC **验证版本与 matcher**，利用由操作者选 `/web-attack`。Fastjson 等具体 CVE 的 PoC 条件写在 vulnerability-intelligence，不要在 SKILL 贴整段 exploit。

---

## 6. 输出

```text
[WEB-RECON] TARGET
stack / WAF:
paths / API:
cve candidates: ID + gate + PoC yes/no
next: waiting operator（候选只认 ~/.claude/skills/shared/modules.yaml）
```
