# CI/CD 自动化审计与人工验证

> 目标：工具负责提高发现率，**结果必须回到人工判断**。不要把“scanner finding”直接当成 exploitable。

---

## 1. 工具定位

| 工具 | 2026定位 | 适用 |
|---|---|---|
| Poutine | 跨平台CI workflow静态扫描 | GitHub/GitLab/Azure DevOps/Tekton |
| Trajan | 多平台检测 + GitHub授权验证 + Graph | GitHub/GitLab/Azure DevOps |
| Octoscan | GitHub Actions专项攻击面静态扫描 | GitHub Actions |
| zizmor | 高精度GitHub Actions/Dependabot/pre-commit审计 | GitHub Actions |
| Harden-Runner | Runtime observation / egress/process/file telemetry | 自有/授权Runner验证 |

**2026状态：** Gato 已归档并由 Trajan 接替；旧笔记里的 Gato 命令只保留历史兼容，不作为新流程主工具。

---

## 2. 推荐顺序

```text
local repo / API read access
        ↓
Poutine / Trajan broad scan
        ↓
GitHub? → Octoscan + zizmor deep scan
        ↓
人工把finding映射到：Trigger → Untrusted Input → Privileged Sink
        ↓
先 marker / dry-run
        ↓
确认 exploitability
```

### Poutine

```bash
poutine analyze_local . --format json > poutine.json
poutine analyze_repo ORG/REPO --token "$GH_TOKEN" --format sarif
```

重点不是 finding 数量，而是组合：

```text
external trigger
+ attacker-controlled data/code
+ self-hosted runner / write token / secrets / OIDC
= 高价值候选
```

### Trajan

```bash
trajan github run ORG/REPO
trajan github report --format html
trajan github graph
```

GitHub Attack Plan：

```bash
trajan github attack plan list
trajan github attack plan validate github/pwn-request
```

- 默认 dry-run；
- `--execute` 前检查 scope/identity/cleanup；
- 内置计划当前包括 pwn-request、comment-injection、cache-poison、stale-approval 等；
- GitLab/Azure DevOps 当前以 detection 为主，不假设已有等价 attack automation。

### Octoscan

```bash
./octoscan dl --token "$GH_TOKEN" --org ORG --repo REPO --default-branch
./octoscan scan octoscan-output --disable-rules shellcheck,local-action --filter-triggers external
./octoscan scan --list-rules
```

高价值规则：`dangerous-checkout`、`dangerous-action`、`dangerous-write`、`expression-injection`、`runner-label`、`repo-jacking`、`bot-check`、`known-vulnerability`、`dangerous-artefact`、`debug-oidc-action`。

### zizmor

```bash
zizmor --collect=workflows,actions .
GH_TOKEN="$(gh auth token)" zizmor ORG/REPO
```

优先看：template injection、cache poisoning、unpinned/ambiguous refs、excessive permissions、credential persistence/artipacked、impostor commits。

---

## 3. Runtime验证：Harden-Runner

Harden-Runner 是观察/限制工具，不是“漏洞扫描器”。在自有测试 workflow 中可以观察：

```text
哪个step访问了外网？
哪个process读取了敏感文件/runner进程？
是否存在非预期package registry / cloud endpoint？
```

它适合确认 build dependency、第三方 Action、agentic workflow 的真实运行行为。

---

## 4. Finding人工判定模板

```text
Finding:
Trigger:
Attacker-controlled source:
Privileged sink:
Token/Secret permissions:
Runner type:
Artifact/cache boundary:
Cloud/K8s deployment identity:
最小验证方法:
成功证据:
Cleanup:
```
