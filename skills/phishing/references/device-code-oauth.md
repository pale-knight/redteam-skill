# Device Code / OAuth Consent

身份钓鱼。先拿到 **可验证 token**，再在本模块内把 token 用到执行/foothold。

2026 犯罪侧有 EvilTokens 等 PhaaS——**红队不要用犯罪套件**。用 TokenTacticsV2、ROADtools/roadtx、GraphRunner。

---

## 1. Device Code

OAuth 2.0 Device Authorization Grant：用户在 **真实 Microsoft 登录页** 输入攻击者生成的短码，攻击者轮询拿到 token。可过密码+MFA；passkey 场景看是否仍允许该 flow。

### TokenTacticsV2

```powershell
git clone https://github.com/f-bader/TokenTacticsV2.git
Import-Module .\TokenTactics.psd1
Get-Command *Token*
# 以当前模块帮助为准
Get-AzureToken -Client MSGraph
```

屏幕上会出现 `user_code` + `https://microsoft.com/devicelogin`。把这两样发给目标（邮件/Teams）。**code 有时效，必须实时生成。**

### roadtx

```bash
pipx install roadlib
roadtx -h
roadtx deviceauth -h
# 以当前 -h 为准启动 device code 并轮询
```

### 验证 token

```bash
# Graph
curl -s -H "Authorization: Bearer $ACCESS" https://graph.microsoft.com/v1.0/me
curl -s -H "Authorization: Bearer $ACCESS" https://graph.microsoft.com/v1.0/me/messages?$top=5
```

`200` + 用户 UPN = token 有效。refresh token 留下，access token 会过期。

Conditional Access 若 **block device code flow**，这条路直接换。

---

## 2. 从 token 打到 shell

```text
读邮件 → 内部二次投递 ClickFix
OneDrive/SharePoint 写诱饵文件
若用户/角色能进 Intune / Endpoint / RMM：推命令
Graph 发 Teams 消息走帮助台/Quick Assist
用 refresh 换 Outlook/Azure 管理面 audience（TokenTactics 的 refresh-to-audience）
```

管理面角色足够时，在本模块把脚本推到设备，拿 shell。全面 Azure IAM 枚举才作为 `/cloud-attack` 候选。

---

## 3. OAuth Consent phishing

攻击者应用要 delegated permissions，用户在真实 consent 屏授予。这不是口令钓鱼；改密码 **不会** 自动撤授权。

```text
1. 授权租户或攻击者租户注册多租户应用（engagement 允许的前提下）
2. redirect URI 指向你控制的回调
3. 权限与诱饵一致（不要一上来 Application.ReadWrite.All 吓跑用户）
4. 构造 authorize URL
5. 用户同意后用 code 换 token
6. Graph 验证
7. 同上，走到执行
```

```text
User consent 关闭 / 必须 admin consent → 这条对普通用户失败
Publisher verification / risky app banner → 降低成功率，不意味着技术失败
```

成功：grant 存在 + token 能打目标 API。然后继续执行入口。

---

## 4. 清理

```text
删除测试 app registration / service principal
撤销 user consent 和 refresh token
记录谁被钓鱼、什么权限、是否已换到 shell
```
