# GCP 提权路径

## 1. Service Account Impersonation

条件：`roles/iam.serviceAccountTokenCreator` 或等价 `iam.serviceAccounts.getAccessToken`。

```bash
gcloud auth print-access-token \
  --impersonate-service-account=<TARGET_SA>
```

验证：用 `--impersonate-service-account` 执行只读 API，确认目标 SA 权限。

## 2. iam.serviceAccounts.actAs

`actAs` 本身通常需要与可指定 service account 的 Compute/Cloud Run/Functions 等资源创建或修改权限组合。

典型思路：

```text
actAs(high-priv SA)
+
create/update execution resource
→ service runs as high-priv SA
```

## 3. setIamPolicy

`resourcemanager.projects.setIamPolicy` / folder/org IAM 修改属于直接高影响权限。

保存当前 policy：

```bash
gcloud projects get-iam-policy <PROJECT> --format=json > iam-original.json
```

任何测试 binding 修改后必须恢复。

## 4. SA Key

条件：`iam.serviceAccountKeys.create`，同时组织策略没有禁止 key creation。

```bash
gcloud iam service-accounts keys create key.json \
  --iam-account=<SA_EMAIL>
```

当前很多组织会通过 `iam.managed.disableServiceAccountKeyCreation`（或 legacy constraint）禁止创建，失败时不要重复尝试，改走 impersonation/workload identity 路径。

## 5. Compute Metadata / Startup Script

条件：能修改 instance metadata。

```bash
gcloud compute instances add-metadata <INSTANCE> \
  --zone <ZONE> \
  --metadata-from-file startup-script=script.sh
```

需考虑脚本是否只在 boot 触发、Guest Agent 状态、实例重启影响。靶场外需谨慎。

## 6. Cloud Functions / Cloud Run

修改代码/配置并指定高权 service account 可能形成执行链。

先记录原 revision/function config 和 execution SA，再做最小验证。

## 7. GKE boundary

可获取 GKE credential → `/k8s` 候选，不在本文件继续 Kubernetes RBAC。
