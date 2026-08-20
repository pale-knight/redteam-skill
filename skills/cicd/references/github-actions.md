# GitHub Actions 攻击链 — 2026

> 目标：从 GitHub Actions 信任边界出发，把当前 CI/CD 攻击链推进到可验证的仓库权限、secret reachability、runner execution、artifact/deploy control 或 cloud identity。

---

## 1. 建图：Trigger → Source → Sink → Privilege

```bash
grep -RniE 'pull_request_target|workflow_run|issue_comment|workflow_call|workflow_dispatch|repository_dispatch|id-token:|permissions:|self-hosted|secrets: inherit|actions/cache|upload-artifact|download-artifact' .github/workflows
```

先标记：

```text
Trigger: pull_request / pull_request_target / workflow_run / issue_comment / push ...
Source : title/body/comment/branch/ref/artifact/output/cache/repo code
Sink   : run:/shell, checkout+build, action input, GITHUB_ENV/OUTPUT, eval/script
Privilege: GITHUB_TOKEN write? secrets? environment? OIDC? self-hosted?
```

---

## 2. `pull_request_target` — Pwn Request + TOCTOU + Cache

危险组合：

```yaml
on: pull_request_target
...
- uses: actions/checkout@v6
  with:
    ref: ${{ github.event.pull_request.head.ref }}
- run: ./build.sh
```

### 判断

```text
pull_request_target
+ fork可触发
+ checkout/下载PR可控代码
+ 执行PR内容
= privileged code execution candidate
```

`head.ref` 是可变branch ref；审批后攻击者仍可能更新分支。检查是否使用固定 `head.sha`，以及 approval/label 后到真正执行之间是否有 TOCTOU。

### 最小验证

在授权测试 fork 中只让 PR 代码产生 marker：

```bash
printf 'CICD_PR_TARGET_PROOF\n' > /tmp/cicd-proof
```

**成功判断：** marker 出现在 base-context workflow 的 job 上；随后再判断 `GITHUB_TOKEN`、secrets、environment、OIDC 是否可达。

### Cache poisoning

即便 `permissions: {}`，如果低信任 job 能写 default-branch 可被高权限 workflow 恢复的 cache，也可能形成第二跳。

检查：

```bash
grep -RniE 'actions/cache|restore-keys|key:' .github/workflows
```

必须证明：

```text
低信任workflow能写入某cache key/prefix
+ 高权限workflow会恢复同一缓存族
+ 恢复内容后来被执行/加载/信任
```

不要把“存在 cache”直接判为漏洞。

---

## 3. `workflow_run` — Privilege Boundary + Artifact Poisoning

`workflow_run` 触发的 workflow 可以拥有不同于上游 workflow 的 secrets/write 权限，因此上游所有输出都应视为不可信。

危险链：

```text
fork PR / low-priv workflow
   ↓ upload artifact/output
workflow_run privileged workflow
   ↓ download/use artifact
shell / script / publish / repo write
```

检查：

```bash
grep -RniE 'workflow_run|download-artifact|gh run download|artifacts' .github/workflows
```

验证时让低权限 artifact 只携带 marker，观察高权限 workflow 是否把 marker 当命令、脚本路径、环境变量、release metadata 或部署输入消费。

其他高危：
- artifact 解压到 workspace 导致文件覆盖；
- artifact 内容写入 `$GITHUB_ENV`/`$GITHUB_OUTPUT`；
- 上游 workflow 名称/branch 检查不够，攻击者可在 PR 中修改上游 workflow 并触发已有 `workflow_run`。

---

## 4. `issue_comment` / IssueOps

危险组合：

```text
issue_comment
+ maintainer comment/command作为gate
+ 根据PR号解析最新head ref
+ checkout并执行PR代码
```

主要问题：TOCTOU。管理员批准后，攻击者可能更新 PR branch；不要只看“谁发了评论”，要看真正执行的是哪个不可变 SHA。

验证：在测试 PR 中先获得批准，然后改变测试 marker，确认 workflow 最终执行的是审批前还是审批后的 commit。

---

## 5. Expression / Template / Environment Injection

典型不可信 source：

```text
github.event.issue.title/body
github.event.pull_request.title/body/head.ref
github.event.comment.body
matrix/outputs/artifact内容
```

危险 sink：

```yaml
- run: echo "${{ github.event.issue.title }}"
```

不要用真实破坏命令；先用 shell 语义 marker 判断是否打破字符串上下文。

同样检查：

```text
GITHUB_ENV
GITHUB_OUTPUT
step outputs
needs.*.outputs
```

如果不可信内容被写入环境/输出后在后续 `run:` 中解释，可能形成间接注入。

Octoscan `expression-injection` / `dangerous-write`、zizmor `template-injection` 优先辅助定位。

---

## 6. Reusable Workflow / `workflow_call`

搜索：

```bash
grep -RniE 'workflow_call|secrets:[[:space:]]*inherit|uses:.*\.github/workflows/' .github/workflows
```

检查四件事：

```text
caller trigger是否低信任？
called workflow ref是否branch/tag而非固定SHA？
secrets: inherit 是否把高价值secret扩大到通用workflow？
caller传入的inputs是否进入run/action/deploy sink？
```

跨仓库 reusable workflow 是一层新的供应链 trust boundary。当前 GitHub 支持 branch/tag/SHA 引用；SHA 最稳定，tag/branch 应进一步审计可变性与维护权限。

---

## 7. Third-party Actions / Mutable Refs / Repo-jacking

```bash
grep -RniE 'uses:[[:space:]]*[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@' .github/workflows
```

分类：

```text
full commit SHA        → 相对强
immutable release tag → 检查项目是否真正启用release immutability
普通tag / branch      → mutable trust
不存在的owner/repo    → repo-jacking candidate
已知漏洞Action        → known-vulnerability candidate
```

GitHub 2025-10 后 immutable releases 已 GA；但**不能看到 `@v1` 就默认 immutable**。确认 release immutability / org policy / exact SHA。

Octoscan：`repo-jacking`、`known-vulnerability`；zizmor：unpinned/confusable/impostor refs。

---

## 8. Dependabot / Bot Identity Trust

危险思想：

```yaml
if: github.actor == 'dependabot[bot]'
```

不要把 bot 名称本身等价成可信输入。Octoscan `bot-check` 会标记相关模式。人工继续确认：攻击者能否在 fork/依赖更新流程中让 bot 生成可控 branch/PR，并触发高权限 job。

---

## 9. GITHUB_TOKEN / App Token / Permissions

```bash
grep -RniE '^permissions:|contents:[[:space:]]*write|pull-requests:[[:space:]]*write|packages:[[:space:]]*write|actions:[[:space:]]*write|id-token:[[:space:]]*write' .github/workflows
```

优先判断最小能力，不要只打印 token：

```bash
gh api repos/ORG/REPO --jq '.permissions'
gh api repos/ORG/REPO/actions/permissions/workflow
```

如果 workflow 能创建/修改代码、release、package、workflow 或 approval，记录为独立能力。

---

## 10. Artifact Secret Leakage / ArtiPACKED类问题

检查 `upload-artifact` 路径是否可能包含：

```text
.git/config
.env / build env dumps
cloud config
npm/pypi credentials
workspace根目录
runner temp/cache
```

现代 `actions/checkout` 已改变 credential persistence 位置（v6+ 更不易把 token直接留在 repo `.git/config`），但不能因此跳过 artifact 检查；混用旧 checkout、自定义 git、workspace 打包仍可能泄露凭据。

可用：

```bash
# 对授权repo的workflow artifact做secret扫描
# 下载后只做本地检查
find artifacts -type f -maxdepth 5 -print
noseyparker scan artifacts/
```

---

## 11. OIDC

见 **workload-identity.md**。`id-token: write` 本身不是漏洞；它是高价值能力提示，必须和 trigger/claims/cloud trust 组合判断。
