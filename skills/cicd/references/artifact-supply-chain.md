# Artifact / Cache / Action / Release 供应链

---

## 1. Artifact Leakage

### 条件

```text
workflow上传artifact
+ path过宽/包含workspace或敏感配置
+ artifact可被攻击者读取
```

```bash
grep -RniE 'upload-artifact|artifact|path:' .github/workflows
```

重点文件：

```text
.git/config
.env
coverage/build logs
cloud CLI config
package manager credentials
workspace debug dumps
```

下载授权repo artifact后本地扫描：

```bash
mkdir -p artifacts
# 使用 gh run download / API按目标run下载
noseyparker scan artifacts/
```

**成功判断：** 得到真实有效且本不应公开/跨边界暴露的 credential 或敏感配置；大量假阳性字符串不算。

---

## 2. Artifact Poisoning

```text
Low-trust workflow
  ↓ attacker-controlled artifact
Privileged workflow (`workflow_run`等)
  ↓ download
execute / source / publish / deploy
```

检查 artifact 是否：
- 被直接 `source` / `bash` / `python` / `node` 执行；
- 覆盖 workspace 文件；
- 影响 package/release metadata；
- 写入 env/output 后被 shell 解释；
- 被签名/发布流程直接信任。

验证先用 marker artifact，不直接投放破坏 payload。

---

## 3. Cache Poisoning

```bash
grep -RniE 'actions/cache|restore-keys|cache-dependency-path' .github/workflows
```

高价值链：

```text
外部/低权限事件可写cache
+ 高权限workflow可restore相同key/prefix
+ restore内容会被执行/加载
```

`restore-keys` 的 prefix fallback 会扩大命中范围；比较 key 中 branch/ref/SHA 是否真正隔离低信任和高权限 workflow。

Trajan 当前自带 `cache-poison` 授权验证计划；zizmor也有 cache-poisoning audit。先 dry-run/marker。

---

## 4. Third-party Action Trust

扫描：

```bash
grep -RniE 'uses:[[:space:]]*[^./][^ ]+@' .github/workflows
```

记录每个引用：

```text
owner/repo
ref = SHA / release tag / major tag / branch
repo ownership
archived/deleted/renamed?
known GHSA/OSV?
是否为 local/composite action?
```

### Repo-jacking

只有当外部 Action 指向不存在/可重新占用的 owner/repo namespace，且 GitHub 的 tombstone/保护机制没有阻止时才成立。Octoscan 可自动验证“owner/org是否存在”，但仍需人工确认可占用性；不要对第三方真实 namespace 做抢注验证。

### Mutable refs

```yaml
uses: vendor/action@main
uses: vendor/action@v1
```

不等于安全。2025-10 GitHub immutable releases 已 GA，但只有真正启用 immutable release 的 release/tag才获得相应保护；否则 full commit SHA 仍是最清晰的 immutable reference。

---

## 5. Release / Provenance / Attestation

现代下游可能检查：

```text
immutable release
artifact attestation
container digest
SLSA provenance
signature / admission policy
```

红队验证应该问：

```text
我能污染artifact，但下游是否按digest/provenance验证？
attestation是不是由同一个可控workflow生成？
registry tag被修改后部署是否仍按digest锁定？
GitOps是否只看tag/latest？
```

不能因为“成功push恶意镜像”就自动判定生产供应链 compromise；必须证明消费者接受它。
