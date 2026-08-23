# 常用字典路径速查

按场景选字典。Kali 自带在 `/usr/share/`，SecLists 是补充集。未装：`apt install seclists`。

**在线喷洒/爆破** 用短列表，并先读锁定策略（`../creds/references/spray-brute.md`）。`rockyou` 给离线 hashcat/john，不要对着域控整份砸。

---

## 路径枚举（目录/文件爆破）

```
# 综合（首选）
/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt      # 目录，30k
/usr/share/seclists/Discovery/Web-Content/raft-medium-files.txt            # 文件，17k

# 大字典（深度扫描）
/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt    # 220k
/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-big.txt       # 1.3M

# 小字典（快速扫描）
/usr/share/wordlists/dirb/common.txt                                       # 4.6k
/usr/share/wordlists/dirbuster/directory-list-2.3-small.txt                # 87k

# 带扩展名
# ffuf/gobuster 用 -e .php,.txt,.html,.bak,.conf,.xml,.json
# 或 -x php,txt,html,bak,conf
```

## API端点

```
/usr/share/seclists/Discovery/Web-Content/api/api-docs.txt                 # Swagger/OpenAPI路径
/usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt
/usr/share/seclists/Discovery/Web-Content/common-api-endpoints-mazen160.txt
```

## 子域名

```
/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt          # 快速
/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt         # 中等
/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt        # 完整
/usr/share/seclists/Discovery/DNS/bitquark-subdomains-top100000.txt
```

## vhost

```
/usr/share/seclists/Discovery/DNS/namelist.txt
# ffuf -H 'Host: FUZZ.target.com' 配合使用
```

## 密码爆破

在线（`/creds` 喷洒）：fasttrack / top-1000 / 目标词 CeWL。轮次间隔跟 **当前 lockout**，不要写死「每天 3 轮」。

离线（hashcat/john）：rockyou + 规则。

```
# 通用（首选）
/usr/share/wordlists/rockyou.txt                                           # 14M，解压: gzip -d rockyou.txt.gz

# 小字典（快速/在线爆破）
/usr/share/wordlists/fasttrack.txt                                         # 222条，常见弱密码
/usr/share/seclists/Passwords/Common-Credentials/10-million-password-list-top-1000.txt
/usr/share/seclists/Passwords/Common-Credentials/best1050.txt

# 中等
/usr/share/seclists/Passwords/Common-Credentials/10-million-password-list-top-100000.txt

# 默认凭据
/usr/share/seclists/Passwords/Default-Credentials/default-passwords.csv
/usr/share/seclists/Passwords/Default-Credentials/ftp-betterdefaultpasslist.txt
/usr/share/seclists/Passwords/Default-Credentials/ssh-betterdefaultpasslist.txt
```

## hashcat规则（密码变形）

```
/usr/share/hashcat/rules/best64.rule                   # 最常用，64条规则
/usr/share/hashcat/rules/rockyou-30000.rule             # 大规则集
/usr/share/hashcat/rules/d3ad0ne.rule                   # 经典
/usr/share/hashcat/rules/OneRuleToRuleThemAll.rule      # 社区最强单规则

# 用法
hashcat --stdout wordlist.txt -r best64.rule > mutated.txt
hashcat -m <type> hash.txt wordlist.txt -r best64.rule
```

## 用户名

```
# 通用用户名
/usr/share/seclists/Usernames/xato-net-10-million-usernames.txt            # kerbrute枚举用
/usr/share/seclists/Usernames/Names/names.txt                              # 名字列表
/usr/share/seclists/Usernames/cirt-default-usernames.txt                   # 默认用户名

# 姓名→用户名格式转换
username-anarchy --input-file names.txt --select-format first.last > users.txt
# 支持格式: first.last / flast / first_last / firstl 等
```

## SNMP

```
/usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt
/usr/share/seclists/Discovery/SNMP/snmp-onesixtyone.txt
# onesixtyone -c <上述文件> TARGET
```

## SQL注入

```
/usr/share/seclists/Fuzzing/SQLi/Generic-SQLi.txt
/usr/share/seclists/Fuzzing/SQLi/Generic-BlindSQLi.txt
# sqlmap自带字典不需要指定
```

## XSS

```
/usr/share/seclists/Fuzzing/XSS/XSS-BruteLogic.txt
/usr/share/seclists/Fuzzing/XSS/XSS-Jhaddix.txt
```

## LFI

```
/usr/share/seclists/Fuzzing/LFI/LFI-Jhaddix.txt
/usr/share/seclists/Fuzzing/LFI/LFI-LINUXList.txt
/usr/share/seclists/Fuzzing/LFI/LFI-WindowsList.txt
```

## 参数名

```
/usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt
# arjun自带字典，通常不需要额外指定
```

---

## 自定义字典

```
# CeWL从目标网站爬关键词
cewl http://target.com -d 3 -m 5 -w custom.txt

# 规则变形
hashcat --stdout custom.txt -r /usr/share/hashcat/rules/best64.rule > mutated.txt

# crunch生成模式字典
crunch 8 8 -t @@@@2026 -o dates.txt          # 4字母+2026
crunch 6 6 -t Lab%%% -o lab.txt              # Lab+3位数字
```

---

## 自有字典（~/tools/wordlists/）

个人收集/定制的字典统一放 `~/tools/wordlists/`，按用途分目录。
当操作者说"用我的字典"或指定自定义字典时，从此目录查找。

```
~/tools/wordlists/
├── dirs/              # 路径枚举
├── passwords/         # 密码爆破
├── usernames/         # 用户名
├── subs/              # 子域名
└── custom/            # 针对特定目标生成的(CeWL输出等)
```

新增字典后在此处登记路径和用途，Claude Code即可按名调用：

```
# 示例（你添加字典后按此格式补充）：
# ~/tools/wordlists/dirs/dirfuzzing.txt        — 综合路径枚举，来源OSCP study guide
# ~/tools/wordlists/passwords/company-weak.txt — 公司常见弱密码模式
```
