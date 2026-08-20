# Dependency / Package Supply Chain

> 目标：证明目标构建/开发环境会解析并执行攻击者控制的依赖。优先使用 benign marker/OOB，避免一开始就做 destructive package。

---

## 1. 先画 Resolver

```text
manifest / lockfile
↓
private registry / proxy / public registry
↓
name + version + scope/namespace
↓
install/build hook
```

搜索：

```bash
find . -maxdepth 4 -type f \( -name 'package.json' -o -name 'requirements*.txt' -o -name 'pyproject.toml' -o -name 'Gemfile' -o -name '*.csproj' -o -name 'NuGet.config' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name '.npmrc' -o -name 'pip.conf' \) -print
```

---

## 2. Dependency Confusion

覆盖：

```text
npm
PyPI
RubyGems
NuGet
crates.io
```

确认三件事：

```text
内部包名在公共源是否可注册？
resolver是否会同时访问公共源？
version/source priority是否会选攻击者版本？
```

### 安全验证包

发布测试包只做 OOB/marker，例如安装时请求唯一 DNS/HTTP 标识，不执行 shell。

**成功判断：** OOB 请求来自目标 CI/build 环境，并能映射到目标 project/job；开发者自己安装测试包不算目标 pipeline compromise。

---

## 3. Go 不套用简单“公共registry同名高版本”模型

Go module 更应检查：

```text
module path / vanity import path
GOPROXY / GOPRIVATE / GONOSUMDB
直接VCS dependency
repo rename/delete / namespace takeover
replace directive
unversioned branch/ref
```

如果攻击点来自 Git/VCS/repository ownership，它更接近 repo-jacking/module-path trust，不要套 npm/PyPI 同名包结论。

---

## 4. Typosquatting / Namespace Confusion

重点不是“名字像”，而是**目标构建是否真的引用**：

```text
misspelling
scope omission
case/normalization difference
registry namespace mapping
internal mirror fallback
```

先通过 lockfile/build log/registry request 证明 resolver 行为。

---

## 5. Package Install Hooks

高价值 hook：

```text
npm preinstall/install/postinstall
Python build backend/setup/build hooks
Ruby gem extensions
NuGet/MSBuild targets
Rust build.rs
```

只有在目标 pipeline 会执行 hook 时才构成代码执行；纯下载但不执行只算供应链控制能力。

---

## 6. Package/Registry Credential

查：

```text
.npmrc / NODE_AUTH_TOKEN
.pypirc / TWINE_*
NuGet.Config
Cargo credentials
GitLab Deploy Token
GitHub Packages token
Artifactory/Nexus/JFrog credential
```

获得 publish 权限后继续验证**目标消费者是否自动拉取该包/版本**，不能把“能发布”直接等于“能RCE”。
