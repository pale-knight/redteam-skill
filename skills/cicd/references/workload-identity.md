# CI Workload Identity / OIDC → Cloud Identity

> 目标：从 CI/CD 信任链出发，至少走到“成功取得实际云身份”。`id-token: write` 或 OIDC Action 只是候选，不是漏洞。

---

## 1. GitHub Actions OIDC发现

```bash
grep -RniE 'id-token:[[:space:]]*write|configure-aws-credentials|azure/login|google-github-actions/auth|aliyun|oidc' .github/workflows
```

典型：

```yaml
permissions:
  contents: read
  id-token: write
```

同时记录：

```text
workflow trigger
repo / org
branch/tag/ref
environment
reusable workflow caller
job permissions
cloud audience / role / service principal / provider id
```

---

## 2. 取得 OIDC Token（授权测试workflow）

GitHub runner 提供：

```text
ACTIONS_ID_TOKEN_REQUEST_URL
ACTIONS_ID_TOKEN_REQUEST_TOKEN
```

在受控 workflow 中请求指定 audience：

```bash
RESP=$(curl -sS -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
  "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=sts.amazonaws.com")
TOKEN=$(printf '%s' "$RESP" | jq -r '.value')
export TOKEN

# 只解码claims，不输出完整token
python3 - <<'PY2'
import os,base64,json
x=os.environ.get('TOKEN','').split('.')
if len(x)>=2:
    p=x[1]+'='*(-len(x[1])%4)
    print(json.dumps(json.loads(base64.urlsafe_b64decode(p)),indent=2))
PY2
```

检查 `sub` / `aud` / repository / ref / environment 等 claim 是否与云侧 trust 条件匹配。

---

## 3. AWS — 链走到 Role

已知道目标 Role ARN 且 trust 接受当前 token 时：

```bash
aws sts assume-role-with-web-identity \
  --role-arn arn:aws:iam::ACCOUNT:role/ROLE \
  --role-session-name cicd-proof \
  --web-identity-token "$TOKEN" \
  --duration-seconds 900
```

成功后用返回的临时凭据：

```bash
AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_SESSION_TOKEN=... \
aws sts get-caller-identity
```

**到拿到真实 Role identity，CI OIDC链已经闭环。** 是否继续做完整 IAM/资源枚举由操作者决定。

---

## 4. Azure / Entra

识别：

```text
azure/login
client-id / tenant-id / subscription-id
auth-type OIDC / federated credential
environment gate
```

核心是证明当前 GitHub OIDC subject 与 Entra App/Managed Identity 的 federated identity credential 匹配，然后通过官方 login/CLI 获得 token并执行只读身份确认。

```bash
az account show
```

不要在 `/cicd` 中继续展开 Azure RBAC/KeyVault/VM 全面利用；拿到实际 Azure identity 即视为当前链完成。

---

## 5. GCP Workload Identity Federation

识别 `google-github-actions/auth`、Workload Identity Provider、Service Account。确认 untrusted workflow 是否能产生被 provider attribute condition 接受的 GitHub OIDC claims。

成功后验证：

```bash
gcloud auth list
gcloud config get-value account
```

---

## 6. Alibaba Cloud RAM OIDC

识别：

```text
GitHub OIDC action / custom STS exchange
RAM OIDC Provider ARN
RAM Role ARN
audience/subject condition
```

当前链成功标准：GitHub workflow OIDC token 被 Alibaba RAM trust 接受并换得 STS 临时身份；再用只读身份 API确认 principal。全面 RAM/ECS/OSS/Function Compute 枚举属于新的云攻击面。

---

## 7. Reusable Workflow + OIDC

`workflow_call` 会改变 subject/claim 与 trust 设计，特别关注：

```text
谁能调用reusable workflow？
caller是否传入environment？
secrets: inherit?
cloud trust约束的是caller还是called workflow？
ref是否固定SHA？
```

OIDC + reusable workflow 不应只扫描单个 YAML；需要跨 workflow 看完整调用链。
