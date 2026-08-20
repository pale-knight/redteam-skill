# CI/CD 攻击面总览

---

## 1. 攻击面矩阵

| 面 | 典型问题 | 结果 |
|---|---|---|
| Source | repo write / branch protection / reusable template | PPE / workflow control |
| Trigger | PR/issue/comment/workflow_run/downstream trigger | low-trust → privileged context |
| Workflow | expression injection / dangerous checkout | runner command execution |
| Token | GITHUB_TOKEN / CI_JOB_TOKEN / System.AccessToken | repo/project/package control |
| Runner | self-hosted persistent state | cross-job credential/deploy identity |
| Artifact | leakage / poisoning | secret exposure / privileged second-stage execution |
| Cache | low→high trust cache | cross-workflow execution |
| Action/Component | mutable refs / repo-jacking / vulnerable action | third-party supply-chain compromise |
| Dependency | confusion / package trust | build-time code execution |
| Registry | image/package write + consumer trust | downstream deployment compromise |
| Workload Identity | OIDC/federation | cloud identity acquisition |
| Agentic | prompt/tool/output trust | agent-driven repo/shell/deploy impact |

---

## 2. OWASP CI/CD风险映射（保留旧结构）

- Flow Control不足 → PPE / branch / approval / trigger trust
- IAM不足 → token/service connection/runner scope
- Dependency Chain Abuse → dependency confusion / third-party components
- PPE → workflow/Jenkinsfile/pipeline template modification
- PBAC不足 → secrets/identity传播
- Credential Hygiene → artifacts/logs/workspace/token persistence
- System Configuration → anonymous/admin/script console/runner isolation
- Third-party Services → Actions/Apps/Components/registries
- Artifact Integrity → artifact/cache/release/provenance
- Logging/Monitoring → runtime observation / audit gaps

---

## 3. 2026升级重点

Black-cat直接带来的增量：

```text
Poutine
Octoscan
artifact leakage
repo-jacking
Harden-Runner runtime observation
多生态 dependency confusion
```

在此基础上新增：

```text
Trajan（Gato/Glato继任）
zizmor
workflow_run / issue_comment / cache poisoning现代模式
reusable workflow + secrets: inherit
immutable release / artifact attestation trust
CI OIDC → AWS/Azure/GCP/Alibaba identity
GitLab新Runner authentication token模型
Azure DevOps templates/service connections/agent pools
Agentic CI/CD / GitHub Agentic Workflows
```
