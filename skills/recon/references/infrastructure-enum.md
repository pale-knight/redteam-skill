# 基础设施服务 — 只读枚举

---

## Docker Remote API — 2375/2376

```bash
curl -s http://TARGET:2375/version | jq
curl -s http://TARGET:2375/info | jq '.Name,.ServerVersion,.SecurityOptions'
curl -s http://TARGET:2375/containers/json | jq '.[].Names'
curl -s http://TARGET:2375/images/json | jq '.[].RepoTags'
```

TLS 2376：

```bash
openssl s_client -connect TARGET:2376 </dev/null
```

不在 Recon 创建 container。

---

## HashiCorp Vault — 8200

```bash
curl -s http://TARGET:8200/v1/sys/health | jq
vault status -address=http://TARGET:8200
```

有 token：

```bash
VAULT_ADDR=http://TARGET:8200 VAULT_TOKEN="$TOKEN" vault token lookup
VAULT_ADDR=http://TARGET:8200 VAULT_TOKEN="$TOKEN" vault secrets list
VAULT_ADDR=http://TARGET:8200 VAULT_TOKEN="$TOKEN" vault auth list
```

只枚举 token policy/capability 和 mounts，不在 Recon 写 secret/policy。

---

## Consul — 8500 / 8300-8302

```bash
curl -s http://TARGET:8500/v1/agent/self | jq '.Config.Datacenter,.Member.Name'
curl -s http://TARGET:8500/v1/catalog/services | jq
curl -s http://TARGET:8500/v1/catalog/nodes | jq '.[].Node'
```

有 ACL token 时通过 header：

```bash
curl -s -H "X-Consul-Token: $TOKEN" http://TARGET:8500/v1/acl/token/self | jq
```

---

## Nomad — 4646

```bash
curl -s http://TARGET:4646/v1/agent/self | jq '.config.Region,.config.Datacenter'
curl -s http://TARGET:4646/v1/nodes | jq '.[].Name'
curl -s http://TARGET:4646/v1/jobs | jq '.[].Name'
```

有 token：

```bash
NOMAD_ADDR=http://TARGET:4646 NOMAD_TOKEN="$TOKEN" nomad acl token self
NOMAD_ADDR=http://TARGET:4646 NOMAD_TOKEN="$TOKEN" nomad job status
NOMAD_ADDR=http://TARGET:4646 NOMAD_TOKEN="$TOKEN" nomad namespace list
```

重点记录 namespace capabilities，尤其 `submit-job`，但 Recon 不提交任务。

---

## etcd — 2379/2380

```bash
ETCDCTL_API=3 etcdctl --endpoints=http://TARGET:2379 endpoint status -w table
ETCDCTL_API=3 etcdctl --endpoints=http://TARGET:2379 member list -w table
```

如果授权允许匿名 read：

```bash
ETCDCTL_API=3 etcdctl --endpoints=http://TARGET:2379 get '' --prefix --keys-only --limit=50
```

发现 Kubernetes key-space 时只记录事实；不要在 Recon 修改 key。

---

## MinIO / S3-compatible — 9000/9001

```bash
curl -si http://TARGET:9000/minio/health/live
curl -si http://TARGET:9000/minio/health/ready
```

有已知凭据：

```bash
mc alias set target http://TARGET:9000 ACCESS SECRET
mc admin info target
mc ls target
```

只读枚举 bucket/policy visibility。
