# Runner / Agent / Build Worker 攻击链

> 目标：判断 CI job 的执行主机是否构成跨 job/repo/环境的持久信任边界，并把 CI/CD 入口走到 runner execution、credential/deployment identity 或 downstream control。

---

## 1. Runner类型先分类

```text
GitHub-hosted ephemeral VM/container
Self-hosted ephemeral/JIT
Self-hosted non-ephemeral
GitHub ARC runner scale set
GitLab shared/group/project runner
Jenkins controller/agent
Azure DevOps Microsoft-hosted/self-hosted agent
K8s-based ephemeral build pod
```

**不要默认 self-hosted = 永久主机，也不要默认 container = 隔离安全。**

---

## 2. GitHub Self-hosted Runner

Repo/API侧：

```bash
gh api repos/ORG/REPO/actions/runners
# org权限允许时
gh api orgs/ORG/actions/runners
```

Workflow侧：

```bash
grep -RniE 'runs-on:.*self-hosted|runs-on:.*\[' .github/workflows
```

Host侧：

```bash
ls -la ~/actions-runner /opt/actions-runner 2>/dev/null
find / -maxdepth 4 \( -name '.runner' -o -name '.credentials' -o -name '.credentials_rsaparams' \) 2>/dev/null
ps aux | grep -E 'Runner.Listener|Runner.Worker' | grep -v grep
```

### 高价值条件

```text
public/fork-triggered workflow能调度到self-hosted runner
runner group开放给多个repo
non-ephemeral runner跨job复用
workspace/cache/temp长期存在
部署凭据、SSH key、cloud config、kubeconfig在runner可见
runner所在内网可访问生产管理面
```

验证先使用 marker，不做主机级持久化。CI链如果已经获得 runner shell 即视为一个完成点；如果操作者选择继续 Host persistence 再使用 `/post`。

---

## 3. GitHub ARC / Kubernetes Runner

GitHub Actions Runner Controller (ARC) 是官方 Kubernetes autoscaling 方案。判断：

```text
runner是ephemeral pod还是复用pod？
runner pod SA/RBAC权限？
挂载哪些Secret/PVC/cache？
是否使用DinD/hostPath/privileged？
job能否接触K8s API/Cloud workload identity？
```

从 CI/CD 入口开始时，可以把链走到“runner workload 获得 K8s/Cloud identity”完成；之后是否全面攻击 cluster/cloud 由人工决定。

---

## 4. GitLab Runner — 2026 token模型

现代 GitLab 使用 **runner authentication token** 注册/认证 Runner，常见前缀 `glrt-`；旧 registration token workflow 已 deprecated，默认新环境不要继续假设“偷 registration token → 直接注册任意 runner”这一老链必定成立。

```bash
cat /etc/gitlab-runner/config.toml
systemctl status gitlab-runner 2>/dev/null
```

关注：

```text
token = glrt-...
executor = shell/docker/kubernetes/custom
privileged = true?
volumes = /var/run/docker.sock?
cache backend
clone_url / environment / pre_build_script / post_build_script
```

泄露 runner auth token 的实际影响取决于 runner 创建方式、GitLab版本和 server-side runner configuration；验证时先查询 runner 是否仍有效及其scope。

---

## 5. Jenkins Agent

```bash
ps aux | grep -iE 'remoting|agent.jar|jenkins' | grep -v grep
find ~ /opt /var -maxdepth 4 -type f \( -name 'agent.jar' -o -name 'secret-file' -o -name 'config.xml' \) 2>/dev/null
```

检查：

```text
Agent label / job assignment
workspace是否跨job保留
共享目录/NFS
controller是否把credential绑定给agent job
Docker socket / K8s pod template
node property / tool installation
```

不要泛化“Agent → Controller逃逸”；只有具体权限、Remoting漏洞或共享信任路径成立时才报告。

---

## 6. Azure DevOps Agent

Host侧重点：

```text
Agent.WorkFolder/_work
credential/config files
service account
Docker/K8s/cloud CLI config
pipeline OAuth token exposure
agent pool scope
```

Pipeline中的 `System.AccessToken` 是当前 job 的身份能力之一；不要把 token 打印出来作为唯一验证，优先用只读 API 判断项目/仓库/build权限。

---

## 7. Cross-job / Cross-repo Trust

统一判断：

```text
Job A（低信任）
 ↓ workspace/cache/toolchain/runner state
Job B（高权限）
 ↓ secrets/deploy identity
```

如果两者共享持久 runner state，就进一步找：

```text
PATH hijack / executable replacement
shared checkout/workspace
package/cache content
shell profile / tool shim
Docker image/cache
build output
```

验证只放无害 marker，确认 Job B 是否读取/执行 Job A 留下的状态。
