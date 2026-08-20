# Client / Web Delivery

## 1. HTML Smuggling / Client-side reconstruction

目标：让浏览器端脚本在客户端重建文件，而不是声称“必定绕过网关”。

```javascript
function saveBlob(name, bytes) {
  const blob = new Blob([bytes], {type:'application/octet-stream'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}
```

真实环境继续观察：

```text
mail/web sandbox
browser reputation
MOTW
SmartScreen/Gatekeeper
endpoint scanning on write/execute
```

只有最后一层“文件写入/执行后被 AV/EDR 杀”才属于 `/edr-bypass`。

## 2. QR / Mobile handoff

QR 是 delivery channel，不是独立 exploitation primitive。

可用于把身份流程从受管终端转移到移动设备，或引导到 AiTM/device-code/consent 链。成功标准仍由后端 attack path 决定。

## 3. Fake download / update / meeting artifacts

重点是目标用户真实业务上下文与平台适配，不要让 lure 与 payload format 绑定：

```text
Windows → exe/msi/archive/script/client action
macOS   → pkg/dmg/archive/Terminal flow
Browser → HTML/URL/session/consent/device-code
```

## 4. Mail controls belong here

```text
SPF/DKIM/DMARC
mail routing
Safe Links / URL rewriting
attachment sanitization
mail reputation
external sender banners
```

这些即使在“阻挡攻击”，仍属于 phishing delivery plane，不属于 `/edr-bypass`。
