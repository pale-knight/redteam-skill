<p align="center">
  <img src="assets/pale0knight.png" alt="redteam-skill" width="300" />
</p>

<h1 align="center">redteam-skill</h1>
<h2 align="center">Based on Kali+Claude code</h2>
<h3 align="center">Semi-automated Redteam Workflow · 红队半自动工作流</h3>

<p align="center"><em style="font-family: Georgia, serif; font-size: 1.2em; color: #777;">Why so serious?</em></p>

<p align="center">
  <a href="https://github.com/pale-knight/redteam-skill/releases"><img src="https://img.shields.io/badge/release-v1.0.0-blue" alt="release"></a>
  <a href="https://github.com/pale-knight/redteam-skill/stargazers"><img src="https://img.shields.io/github/stars/pale-knight/redteam-skill?style=flat&logo=github" alt="stars"></a>
  <a href="https://github.com/pale-knight/redteam-skill/forks"><img src="https://img.shields.io/github/forks/pale-knight/redteam-skill?style=flat&logo=github" alt="forks"></a>
  <a href="https://github.com/pale-knight/redteam-skill/issues"><img src="https://img.shields.io/github/issues/pale-knight/redteam-skill?style=flat&logo=github" alt="issues"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license"></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/changelog-Keep%20a%20Changelog-orange" alt="changelog"></a>
</p>

<p align="center">
  🌐 <a href="README_en.md">English</a> ·
  <a href="README_ja.md">日本語</a>
</p>

<a id="关于项目"></a>
## 关于项目

> **辅助红队工作，操作者通过`/module`选择模块，AI将取得的成果记录在`notes.md`中供操作者研判并建议下一模块，并在自身无法做到需要操作者辅助，例如：监听/sudo/输密码/Permission denied等情况时停止并等待操作者完成**

本项目面向**红队工作 / 靶场 / HTB** 等场景，提供半自动红队工作流。

做成半自动是因为真实红队中，合格的渗透人员必须根据现场情况做研判并选择下一步，而不是把整条链路交给 AI。AI 可能执行不该执行的动作或者漏掉重要的信息，并无法承担相应的责任和带来的后果。所以也没有限制目标授权的范围，这也应该交由渗透人员负责。

此项目集成了绝大部分技能模块、最近工作中的高成功率利用链，以及 2025–2026 较新的技术路径，并会持续更新。

为了缩短上下文，节约token。此项目将每一模块的重要发现和成果记录在`notes.md`中，当前模块结束时可由人工`/clear`清除上下文。在每一个模块开始时会自动读取`notes.md`中数据，以保证工作延续。并且将每一模块的详细操作流程放入`references`中，只在遇到时才会读取对应的`references/<file>.md`。

<a id="项目架构"></a>
## 项目架构

### 基本架构

18 个模块,每个模块为`SKILL.md`(判断基本方向)和一个`references/`(详细操作流程)。

```text
CLAUDE.md                  # 全局规则,放进项目目录使用
skills/
├── recon/                     # 通用信息收集
│   ├── SKILL.md
│   └── references/     (11)
├── service-attack/            # 服务漏洞利用
│   ├── SKILL.md
│   └── references/     (13)
├── web-recon/                 # Web攻击面测绘
│   ├── SKILL.md
│   └── references/     (5)
├── web-attack/                # Web漏洞利用
│   ├── SKILL.md
│   └── references/     (24)
├── ad-recon/                  # AD枚举
│   ├── SKILL.md
│   └── references/     (5)
├── ad-attack/                 # AD攻击利用
│   ├── SKILL.md
│   └── references/     (9)
├── cloud-recon/               # AWS/Azure/GCP/阿里云枚举
│   ├── SKILL.md
│   └── references/     (7)
├── cloud-attack/              # 云控制面利用
│   ├── SKILL.md
│   └── references/     (9)
├── k8s/                       # 容器与集群
│   ├── SKILL.md
│   └── references/     (6)
├── cicd/                      # CI/CD与供应链
│   ├── SKILL.md
│   └── references/     (12)
├── phishing/                  # 钓鱼和客户端攻击
│   ├── SKILL.md
│   └── references/     (8)
├── privesc-win/               # Windows提权
│   ├── SKILL.md
│   └── references/     (5)
├── privesc-linux/             # Linux提权
│   ├── SKILL.md
│   └── references/     (5)
├── creds/                     # 凭据攻击
│   ├── SKILL.md
│   └── references/     (7)
├── post/                      # 后渗透利用与C2
│   ├── SKILL.md
│   └── references/     (7)
├── shell/                     # shell稳定化
│   ├── SKILL.md
│   └── references/     (6)
├── tunnel/                    # 内网穿透
│   ├── SKILL.md
│   └── references/     (7)
├── edr-bypass/                # AV/EDR规避
│   ├── SKILL.md
│   └── references/     (12)
├── shared/                    # 跨模块共享
│   ├── modules.yaml           # 模块目录
│   ├── cve-enrichment.md      # 全Skill漏洞情报入口
│   ├── tools.md               # 工具注册表
│   └── wordlists.md           # 字典路径
└── bin/
    ├── modules.py             # tail / list / show / check,模块控制和收尾
    └── notes.py               # init / validate,操作记录文件notes.md
```
> `references/`内共 158 份操作文档,按`SKILL.md` 判断选择加载,不计入常驻上下文。

### 模块介绍

| 场景 | 入口 | 类型 | 功能 | 成功条件 | 默认下一步 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 通用信息收集 | `/recon` | recon | 资产扩展、主机与端口发现、服务版本识别、只读枚举、CVE 候选研判 |服务地图 + CVE候选 | `/web-recon` `/ad-recon` `/service-attack` `/phishing` |
| 服务漏洞利用 | `/service-attack` | attack | 数据库、文件与远程访问、消息队列、DNS、网络设备与BMC等利用链 | 对应服务的foothold或shell | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| Web攻击面测绘 | `/web-recon` | recon | 指纹、路径与 API 发现、JS/sourcemap、代理缓存边界、WAF、CMS | Web攻击面卡片 | `/web-attack` |
| Web漏洞利用 | `/web-attack` | attack | 注入、上传、LFI、SSRF/XXE/SSTI、反序列化、JWT/SAML、走私、WAF 绕过等利用链 | foothold、shell或等价OS执行 | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| 域枚举 | `/ad-recon` | recon | 获取用户组机器、ACL/委派、ADCS、LAPS、BloodHound、信任图等 | 域路径与 ACL 卡片 | `/ad-attack` `/creds` |
| 域攻击利用 | `/ad-attack` | attack | Kerberos、委派、强制认证与中继、ACL 滥用、ADCS ESC 全系、dMSA、横向等攻击 | DA、等价域控制,或目标主机SYSTEM | `/ad-recon` `/creds` `/post` `/privesc-win` |
| 云身份枚举 | `/cloud-recon` | recon | 获取AWS/Azure/GCP/阿里云的身份、IAM、信任、资源、元数据等 | 云身份、权限、信任、资源图 | `/cloud-attack` `/k8s` |
| 云控制面利用 | `/cloud-attack` | attack | IAM 提权、身份假冒、跨账户信任、serverless、云原生持久化 | 更高云身份、账户控制,或可下发OS执行的 compute | `/cloud-recon` `/k8s` `/post` `/ad-recon` |
| 容器与集群 | `/k8s` | attack | RBAC 滥用、secrets、kubelet/etcd、容器逃逸、云身份绑定、集群持久化等 | cluster-admin、node root,或可用的云身份 | `/cloud-recon` `/post` `/privesc-linux` `/creds` |
| CI/CD 与供应链 | `/cicd` | attack | Jenkins、GitHub Actions、GitLab/ADO、runner、依赖混淆、registry 投毒、OIDC等利用 | runner shell、部署控制,或可独立使用的新身份 | `/cloud-recon` `/privesc-linux` `/privesc-win` `/post` |
| 钓鱼与客户端攻击 | `/phishing` | attack | ClickFix/FileFix、AiTM 会话、device code/OAuth、helpdesk 社工、文件投递等攻击 | host shell或foothold | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| Windows 提权 | `/privesc-win` | attack | Potato家族、令牌特权、服务/DLL/计划任务、UAC、内核LPE等方式 | Administrator(High IL)或NT AUTHORITY\SYSTEM | `/creds` `/post` `/ad-recon` `/tunnel` |
| Linux 提权 | `/privesc-linux` | attack | sudo/GTFOBins、polkit、SUID/capabilities、systemd、危险组、内核LPE等方式 | uid=0 root shell | `/creds` `/post` `/k8s` `/cloud-recon` |
| 凭据攻击 | `/creds` | factory | secret发现、离线破解、按策略喷洒、NetNTLM捕获与SMB relay、系统凭据收割 | 经校验的可用凭据 | `/ad-recon` `/cloud-recon` `/service-attack` `/privesc-win` `/privesc-linux` `/post` |
| 后渗透与C2 | `/post` | post | 主机画像、host-native持久化、Sliver C2、定向收集外带、清理 | 所选目标已验证（回连/persist/loot/已还原） | `/tunnel` `/creds` `/ad-recon` `/cloud-recon` |
| shell 稳定化 | `/shell` | support | 回连引导、Linux PTY、Windows ConPTY、监听管理、会话恢复、文件传输 | 可操作稳定会话 | `/privesc-win` `/privesc-linux` `/creds` `/post` |
| 内网穿透 | `/tunnel` | support | ligolo-ng、chisel、GOST、原生转发、Dev Tunnels、多跳、备用传输 | 目标网段可达 | `/recon` `/service-attack` `/ad-recon` |
| AV/EDR规避 | `/edr-bypass` | interceptor | 将被AV/EDR/AMSI/WDAC/PPL/内存/内核遥测的拦截变为可执行 | 被拦动作可执行 | 回原模块 |
> `recon` 模块信息收集以确认攻击面，`attack` 模块执行攻击链获取对应控制权，`support` 模块不推进攻击链只稳固当前shell，`factory` 模块仅有`/creds` 只校验凭据，`post` 模块仅有`/post`只做收尾工作，`interceptor` 模块仅有`/edr-bypass`只在被拦截时执行，在绕过拦截之前切回原模块继续执行。

<a id="使用说明"></a>
## 使用说明

### 前置依赖

- **Kali Linux** — 推荐环境，工具链默认按Kali路径和 `shared/tools.md` 内容安装
- **Python 3.x** — 运行 `bin/modules.py`、`bin/notes.py`
- **Claude Code** — 本 Skill 面向 Claude Code 设计，模块经 `/slash` 命令调用

### 目录层级

**工作目录** 
```text
~/ops/<target>/
├── CLAUDE.md                  # 工作规则
├── notes.md                   # 工作记录
└── scans/  loot/  scripts/    # 工作产出
```
> 可以自己建立或者让AI自动创建。

**工具目录**
```text
~/tools/
├── recon/
├── web/
├── ad/
...
├── c2/
├── edr/
└── shell/
```
> 详情见`shared/tools.md`。

### 安装

    git clone https://github.com/pale-knight/redteam-skill.git
​> 把18个模块、`shared/`和`bin/`移动到`~/.claude/skills/`skill的全局目录，`CLAUDE.md`放入每个项目目录。

### 开始

```text
mkdir -p ~/ops/<target> && cd ~/ops/<target>
cp CLAUDE.md ./CLAUDE.md
```
创建`notes.md`
```text
python ~/.claude/skills/bin/notes.py init
```
单次工作流程
```text
操作者   /<module>
AI      Read ./notes.md
        阅读SKILL.md
        走到对应流程，才读取对应的references/<file>.md
        做到本模块成功条件
        需要操作者协助时 → 立刻停，说明需要做什么，等待回复
        半路发现其他面 → 只记 notes，不跳模块
        追加 ./notes.md
        python ~/.claude/skills/bin/modules.py tail <module>
        列1–3条候选（写清凭notes哪些记录）→ 停止
操作者   根据当前情况选择路径，或/clear后再/module开始下一个模块
```

## 联系方式

- **x**：@Evander0L
- **问题反馈**：[GitHub Issues](https://github.com/pale-knight/redteam-skill/issues)

## 免责声明

本项目仅限用于合法的安全研究、教育、靶场、HTB，以及对自有系统或已获得明确授权的目标进行测试。

**严禁在未经授权的情况下访问、扫描、利用、干扰目标或获取数据。** 使用者须自行确保其行为符合适用法律法规及授权范围；因滥用本项目造成的任何损失或法律责任，均由使用者自行承担，项目维护者不承担相关责任。
