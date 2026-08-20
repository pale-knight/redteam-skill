---
name: cicd
description: "CI/CD pipeline and software-supply-chain exploitation: Jenkins, GitHub Actions, GitLab CI/CD, Azure DevOps, Gitea/Forgejo, self-hosted runners/agents, poisoned pipeline execution, artifact/cache abuse, dependency confusion, third-party Action trust, GitOps/registry poisoning, workload identity/OIDC, and emerging agentic CI/CD. Use this skill when the operator has access to a CI/CD system, source repository, build/deploy configuration, runner/agent, artifact/package/registry path, or software delivery trust chain."
---

# /cicd — CI/CD管道攻击 + 软件供应链

> **scope：** 从代码仓库、Workflow/Pipeline、Runner/Agent、Artifact/Package、Build/Deploy 信任链出发，完成 CI/CD 视角下的攻击链验证。链可以自然跨到 Host、Cloud、K8s，但不要仅因为协议/API变化就中途停止；当已经取得一个可独立使用的新身份/控制能力（如 Runner Shell、Cloud Role、K8s部署控制）时，记录结果并把其他模块作为**人工可选方向**。本模块不做自动路由或自动状态切换。

工具安装问题参阅 `../shared/tools.md`。**禁止开局把 references/ 全读。** 不知道打哪条供应链时才 Read `references/cicd-attacks.md` 总览；已经知道是 GitHub/Jenkins/Runner/OIDC 则直接读对应那一份。产品 CVE 有精确版本才 `../shared/cve-enrichment.md` + `references/vulnerability-intelligence.md`。

本模块是红队攻击模块。默认打到 **Runner Shell / 部署控制 / 真实 Cloud Identity**。PPE、cache poison、OIDC 换票都要真正执行（先 marker 再实弹），不要停在静态扫描高危结果。

---

## 开局与收尾

开局第一件事：Read `./notes.md`。没有则 `python ~/.claude/skills/bin/notes.py init`。只按已拿下/凭据继续。
走到哪条链，才 Read **一份** `references/<file>.md`。禁止开局全读、禁止凭记忆写 payload。
监听 / sudo / 输密码 / Permission denied：立刻停，说明等操作者做什么，等回报。不要假装已成功。
收尾：
1. 追加 `./notes.md`
2. `python ~/.claude/skills/bin/modules.py tail <本模块名>`
   Read 备用：`~/.claude/skills/shared/modules.yaml`
   禁止 `./modules.yaml` 和 `python ../bin/...`
3. 优先 `default_next`；`never_default` 不得当作默认（操作者点名除外）
4. 名册外的名字不许建议
5. 停。等操作者选 `/模块` 或 `/clear`
`/edr-bypass` 半条链未完：打通后回本模块，不要 /clear。


---

## 0. 工作方式与成功条件

CI/CD不是“平台产品清单”，而是攻击者对**代码 → 构建 → 制品 → 部署**信任链的利用。

```text
Repo / Workflow / Pipeline / Runner / Artifact / Registry / Deploy Identity
                              ↓
                         枚举信任边界
                              ↓
               找低信任输入 → 高权限执行上下文
                              ↓
         证明代码执行 / Secret Reachability / Artifact Control
                              ↓
             Runner Shell / Deployment Control / Cloud Identity
                              ↓
                       当前CI/CD链闭环
```

**成功条件之一：**
- 获得 CI 平台管理/写权限；
- 让受控输入进入高权限 Workflow/Build；
- 在 Runner/Agent 上执行受控命令；
- 读取本不应暴露的 CI Secret/Token；
- 控制 Artifact/Package/Image 并被下游消费；
- 通过 CI workload identity 成功换取真实 Cloud Identity；
- 通过 GitOps/Deploy Pipeline 让目标环境接受受控变更。

**验证优先：** 先使用 marker、OOB、只读 API、临时测试分支/工件证明 primitive；需要修改目标的步骤记录原状态并提供 cleanup。

---

## 0.4 自动漏洞库 / CI-CD Vulnerability Enrichment

对以下对象做版本化漏洞查询：

```text
Jenkins/GitLab/Azure DevOps Server/Gitea/Argo CD等 self-hosted product
runner/agent/plugin/component
third-party Action
repo dependency / build package
```

```bash
cvemap -p jenkins -s critical,high -f age,kev,epss,poc,template
osv-scanner scan -r .
```

完整 → `../shared/cve-enrichment.md` 与 `references/vulnerability-intelligence.md`。

---

## 0.5 Endpoint Defense Boundary — 可选 /edr-bypass Handoff

`/cicd` 自己拥有 Repo/Workflow/Pipeline/Runner/Artifact/Deploy trust chain，直到 Runner Shell / Deployment Control / Cloud Identity 等真实结果。

以下属于 CI/CD 自身：

```text
workflow permissions
branch/environment approval
runner group/trust
secret scope
artifact/cache trust
service connection / workload identity policy
```

只有 pipeline/runner **已经能够执行攻击者控制的命令**，但 runner endpoint 的 AV/EDR/AMSI/WDAC/memory telemetry 阻断当前 payload 时：

```text
CI execution primitive confirmed
→ endpoint defense blocks intended action
→ operator may select /edr-bypass
→ restore execution capability
→ return /cicd
→ finish Runner Shell / downstream control
```

---

## 1. 配置发现 + 自动化候选

先找流水线文件，再静态审计。**CLI 全书 → `references/automation-audit.md`**（Poutine / Trajan / Octoscan / zizmor）。Scanner finding ≠ 可利用。

```bash
find . -maxdepth 4 -type f \( \
  -path '*/.github/workflows/*' -o \
  -name '.gitlab-ci.yml' -o -name 'Jenkinsfile' -o \
  -name 'azure-pipelines.yml' -o -name 'bitbucket-pipelines.yml' -o \
  -name 'buildspec.yml' -o -name 'action.yml' -o -name 'action.yaml' \
\) -print
```

顺序：Poutine/Trajan 广扫 → GitHub 再 Octoscan/zizmor → 人工映射 Trigger → Untrusted Input → Privileged Sink → marker。Trajan Attack Plan 默认 dry-run。

GitHub 利用细节 → `references/github-actions.md`。

---

## 2. Jenkins — Controller / Job / Credential / Agent

```bash
# 指纹/匿名API
curl -sI http://JENKINS:8080/ | grep -iE 'x-jenkins|x-hudson'
curl -s http://JENKINS:8080/api/json?pretty=true

# 已授权/已登录后检查控制面
curl -s -u 'USER:TOKEN' http://JENKINS:8080/api/json?tree=jobs[name,url,color]
```

如果拥有 Script Console 权限，先用无害命令证明 server-side execution：

```groovy
println "whoami".execute().text
println System.getenv().keySet().sort()
```

Jenkinsfile/PPE、Credential Store、Agent/Workspace/Shared Library、Controller路径 → **references/jenkins.md**

---

## 3. GitHub Actions — 现代高价值链

优先检查：

```text
pull_request_target + untrusted checkout
workflow_run + untrusted artifact/output/cache
issue_comment / IssueOps + PR checkout + TOCTOU
expression/template injection
GITHUB_ENV / GITHUB_OUTPUT injection
self-hosted runner / runner group
reusable workflow + secrets: inherit
third-party action mutable ref / repo-jacking / known vulnerable action
artifact leakage / credential persistence / cache poisoning
id-token: write / OIDC cloud identity
Dependabot/bot identity trust
```

不要只看默认分支：非默认分支上的旧 workflow 也可能仍然能被外部事件触发。

完整检查与验证 → **references/github-actions.md**

---

## 4. GitLab CI/CD + Azure DevOps

GitLab重点：

```text
.gitlab-ci.yml / include / CI/CD Components
protected variables / protected refs
CI_JOB_TOKEN scope & allowlist
parent-child / multi-project pipeline
trigger token / deploy token
Runner authentication token (glrt-*)
shared/specific runner trust
artifact/cache/dependency proxy/container registry
```

Azure DevOps重点：

```text
azure-pipelines.yml / templates
Variable Groups / Secure Files
Service Connections
Agent Pools / self-hosted agents
System.AccessToken
Pipeline Resources / completion triggers
Artifacts / feeds / container registry
```

自动审计优先 Trajan + Poutine；具体判断 → **references/gitlab-azuredevops.md**

---

## 5. Runner / Agent / Build Worker

Runner不是“拿到一台普通主机”这么简单；需要先判断它是否跨 repo/job 复用、是否保留 workspace/cache/credential、能否接触部署身份。

```bash
# GitHub runner常见位置
ls -la ~/actions-runner /opt/actions-runner 2>/dev/null
find / -maxdepth 4 -name '.runner' -o -name '.credentials' -o -name '.credentials_rsaparams' 2>/dev/null

# GitLab Runner
cat /etc/gitlab-runner/config.toml 2>/dev/null

# Jenkins
find /var/lib/jenkins /var/jenkins_home -maxdepth 3 -type f 2>/dev/null | head
```

不要把 non-ephemeral 和 ephemeral runner 混为一谈；GitHub ARC/JIT runner 也单独判断生命周期。

完整 Runner/Agent 链 → **references/runner-agent.md**

---

## 6. Artifact / Cache / Third-party Action / Release供应链

把原来的“Artifact Poisoning”拆成四类：

```text
Artifact Leakage   → 工件意外打包token/.git/config/env/config
Artifact Poisoning → 低信任workflow生成内容，被高权限workflow消费
Cache Poisoning    → 低权限上下文写cache，高权限workflow恢复并执行/信任
Release/Action Trust → mutable tag/ref、repo-jacking、第三方Action、release integrity
```

GitHub 2025+ 已支持 immutable releases / artifact attestations；红队判断不再只问“能不能push tag”，还要判断下游**是否实际验证 provenance / digest / immutable ref**。

详细 → **references/artifact-supply-chain.md**

---

## 7. Dependency / Package Supply Chain

不要只覆盖 npm/PyPI：

```text
npm / PyPI / RubyGems / NuGet / crates.io
Git module/VCS dependency/vanity path（Go单独判断，不机械套公共registry同名抢注）
internal package registry fallback
package manager source priority
build-time install hooks
```

验证优先使用 benign marker / DNS-HTTP OOB，确认“目标构建环境确实拉取了攻击者控制的依赖”再决定后续。

详细 → **references/dependency-supply-chain.md**

---

## 8. GitOps / Registry / Deployment Chain

```text
Repo write
  ↓
Pipeline / GitOps source
  ↓
Artifact / Container Registry
  ↓
ArgoCD / Flux / Deploy Job
  ↓
目标环境接受受控版本
```

本模块可以把“CI/CD入口 → 下游部署接受变更”走完；如果已经取得独立 K8s Cluster/Admin、Cloud IAM 身份或 Host Shell，后续全面枚举/提权仍由操作者决定是否选择其他模块。

ArgoCD/Gitea/Forgejo/Registry → **references/gitops-registry.md**

---

## 9. CI Workload Identity / OIDC → Cloud Identity

现代流水线越来越少长期保存 AK/SK，而是：

```text
GitHub/GitLab/Azure DevOps Job
       ↓ OIDC / Federation
AWS Role / Azure Identity / GCP WIF / Alibaba RAM Role
```

从 `/cicd` 视角，链至少走到：**确认 workflow 能请求 token → claims 可控/满足 trust → 成功取得真实云身份**。取得身份后全面 IAM 枚举默认候选 **`/cloud-recon`**，由操作者决定是否再选 `/cloud-attack`。

详细 → **references/workload-identity.md**

---

## 10. Agentic CI/CD（2026 Emerging / Research）

GitHub Agentic Workflows 已把 AI agent 直接放进 GitHub Actions。新增攻击面：

```text
Issue / PR / Comment / Repo Content（不可信）
            ↓
Agent Prompt / Context
            ↓
Agent tools / generated output
            ↓
repo write / command / downstream script / secret access
```

重点判断 Prompt-to-Agent 与 Prompt-to-Script 数据流；先做无害 marker 验证，不把普通 prompt injection 自动等价成 RCE。

详细 → **references/agentic-cicd.md**

## 完成后

写入 `./notes.md`。候选只按「开局与收尾」跑 `python ~/.claude/skills/bin/modules.py tail`。
