# GitLab CI/CD + Azure DevOps

---

# Part A — GitLab CI/CD

## 1. 配置/关系枚举

```bash
find . -maxdepth 4 -type f \( -name '.gitlab-ci.yml' -o -name '*.gitlab-ci.yml' \) -print
grep -RniE 'include:|trigger:|needs:|CI_JOB_TOKEN|artifacts:|cache:|id_tokens:|identity:|secrets:' . 2>/dev/null
```

重点关系：

```text
root pipeline
├─ include local/project/remote/component
├─ parent-child pipeline
└─ multi-project downstream pipeline
```

不要只审根 `.gitlab-ci.yml`。

---

## 2. CI_JOB_TOKEN

`CI_JOB_TOKEN` 是 job 启动时生成、job结束后撤销的短期身份。实际价值取决于 job token allowlist / fine-grained permissions /目标project配置。

在授权job中优先用只读 API 判断 scope，而不是把 token 写入日志。

检查：

```text
当前job能访问哪些project/package/container/artifact/API？
目标project是否允许当前project的job token？
是否存在跨project artifact/package trust？
```

---

## 3. Runner Token现代化

2026 不要继续把“registration token”当默认模型：
- Runner authentication token 是推荐方式，常见 `glrt-`；
- legacy registration tokens 已 deprecated，GitLab 17+ 默认流程已经变化，预计 GitLab 20 删除。

```bash
cat /etc/gitlab-runner/config.toml
```

确认 token 类型、runner scope、executor 和 server-side config 后再判断能否注册/冒用/接收 job。

---

## 4. Protected Variables / MR Pipeline

检查：

```text
variable是否protected/masked/hidden？
job在哪些refs运行？
MR来自fork还是同repo？
merge result pipeline / merged results / protected branch条件？
```

只有证明低信任输入能进入能够读取 protected variable 的 job，才算 secret reachability。

---

## 5. Parent/Child / Multi-project / Component Supply Chain

检查：

```text
include:project ref是否固定？
CI/CD component version/ref是否可变？
trigger是否forward variables？
child能否下载parent artifact？
多项目pipeline下游是否权限更高？
```

GitLab 17.7+ 推荐 typed CI/CD inputs 代替随意 pipeline variables；发现现代 inputs 时检查类型/option validation，同时继续关注传入值最终是否进入 shell/deploy sink。

---

# Part B — Azure DevOps

## 6. 自动审计

```bash
export TRAJAN_ADO_TOKEN="$ADO_PAT"
trajan ado run ORG/PROJECT
```

Poutine 也支持 Azure DevOps pipeline syntax。

---

## 7. YAML / Template Trust

```bash
find . -maxdepth 5 -type f \( -name 'azure-pipelines.yml' -o -name '*pipeline*.yml' -o -name '*pipeline*.yaml' \) -print
grep -RniE 'template:|extends:|resources:|repositories:|serviceConnection|System.AccessToken|variable group|secureFile' . 2>/dev/null
```

检查：

```text
template repo/ref可写吗？
pipeline resource completion trigger能被低信任pipeline触发吗？
Variable Group / Secure File对哪些pipelines授权？
Service Connection是否“grant access to all pipelines”？
Agent Pool是否跨project共享？
```

---

## 8. `System.AccessToken`

如果 job 开启 OAuth token 访问，判断 Build Service identity 的实际 repo/project/package权限。先做只读 API 证明，不默认等于项目管理员。

---

## 9. Service Connection

Service Connection 是 CI/CD 到 Cloud/K8s/Registry 的核心部署身份。CI/CD视角要完成：

```text
低信任pipeline/模板是否能引用该Service Connection？
能否让job以该连接执行受控部署/身份验证？
取得的实际Cloud/K8s identity是什么？
```

走到身份/部署控制确认后，当前CI链闭环；后续全面云/K8s攻击由人工决定。
