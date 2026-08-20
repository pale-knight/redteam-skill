# GCP Cloud-native Persistence

## 1. IAM Binding

最直接的云控制面持久化之一。

保存原 IAM：

```bash
gcloud projects get-iam-policy <PROJECT> --format=json > iam-original.json
```

授权靶场最小验证：

```bash
gcloud projects add-iam-policy-binding <PROJECT> \
  --member='serviceAccount:<CONTROLLED_SA>' \
  --role='<ROLE>'
```

清理：

```bash
gcloud projects remove-iam-policy-binding <PROJECT> \
  --member='serviceAccount:<CONTROLLED_SA>' \
  --role='<ROLE>'
```

## 2. Service Account Key

条件型 persistence：组织策略可能禁止新 key。

```bash
gcloud iam service-accounts keys list --iam-account=<SA>
gcloud iam service-accounts keys create redteam-key.json --iam-account=<SA>
```

清理：

```bash
gcloud iam service-accounts keys delete <KEY_ID> --iam-account=<SA>
```

优先记录 key id，不要把 JSON key 留在共享目录。

## 3. Service Account Impersonation Path

如果已有长期控制的 principal 被授予 Token Creator 到高权 SA，这是一种无需创建 SA key 的持续云身份路径。

通过 IAM binding 建立/验证，结束时删除对应 binding。

## 4. Serverless persistence

Function/Cloud Run service 的代码、revision、execution service account、IAM policy 改动都可形成平台原生持续执行/访问能力。

原则：保存原 revision/config → 最小验证 → 回滚。

## 5. Detection

重点看 Cloud Audit Logs：IAM policy updates、SA key creation、function/run deployment、service account changes。
