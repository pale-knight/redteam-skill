<p align="center">
  <img src="assets/pale0knight.png" alt="redteam-skill" width="300" />
</p>

<h1 align="center">redteam-skill</h1>
<h3 align="center">Based on Kali+Claude code</h1>
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

> **辅助红队工作，人工通过`/module`选择模块，工作流将取得的成果供人工研判并建议下一模块**

本项目面向**红队工作 / 靶场 / HTB** 等场景，提供半自动红队工作流。

做成半自动是因为真实红队中，合格的渗透人员必须根据现场情况做研判并选择下一步，而不是把整条链路交给 AI。AI 可能执行不该执行的动作或者漏掉重要的信息，并无法承担相应的责任和带来的后果。所以也没有限制目标授权的范围，这也应该交由渗透人员负责。

此项目集成了绝大部分技能模块、最近工作中的高成功率利用链，以及 2025–2026 较新的技术路径，并会持续更新。

<a id="项目架构"></a>
## 项目架构

### 基本架构

18 个模块,每个模块为`SKILL.md`(判断基本方向)和一个 `references/`(详细操作文档)。

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
├── ad-recon/                  # 域枚举
│   ├── SKILL.md
│   └── references/     (5)
├── ad-attack/                 # 域利用
│   ├── SKILL.md
│   └── references/     (9)
├── cloud-recon/               # AWS/Azure/GCP/阿里云枚举
│   ├── SKILL.md
│   └── references/     (7)
├── cloud-attack/              # 云权限提升与持久化
│   ├── SKILL.md
│   └── references/     (9)
├── k8s/                       # 容器与集群枚举及利用
│   ├── SKILL.md
│   └── references/     (6)
├── cicd/                      # CI/CD与供应链枚举及利用
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
├── tunnel/                    # 内网端口转发与隧道
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
> `references/` 内共 158 份操作文档,按 `SKILL.md` 判断选择加载,不计入常驻上下文。

### 模块介绍

| 场景 | 入口 | 类型 | 功能 | 成功条件 | 默认下一步 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 通用信息收集 | `/recon` | recon | 资产扩展、主机与端口发现、服务版本识别、只读枚举、CVE 候选研判 |服务地图 + CVE候选 | `/web-recon` `/ad-recon` `/service-attack` `/phishing` |
| 服务漏洞利用 | `/service-attack` | attack | 数据库、文件与远程访问、消息队列、DNS、网络设备与BMC等利用链 | 对应服务的foothold或shell | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| Web攻击面测绘 | `/web-recon` | recon | 指纹、路径与 API 发现、JS/sourcemap、代理缓存边界、WAF、CMS | Web攻击面卡片 | `/web-attack` |
| Web漏洞利用 | `/web-attack` | attack | 注入、上传、LFI、SSRF/XXE/SSTI、反序列化、JWT/SAML、走私、WAF 绕过等利用链 | foothold、shell或等价OS执行 | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| 域枚举 | `/ad-recon` | recon | 路径 / ACL / 证书 / LAPS 卡片 | `/ad-attack` `/creds` |
| 域利用 | `/ad-attack` | attack | 目标身份 / DA / 主机 SYSTEM | `/ad-recon` `/creds` `/post` `/privesc-win` |
| 云身份枚举 | `/cloud-recon` | recon | 云身份与信任图 | `/cloud-attack` `/k8s` |
| 云权限提升与持久化 | `/cloud-attack` | attack | 更高云身份或可下发 OS 的 compute | `/cloud-recon` `/k8s` `/post` `/ad-recon` |
| 容器与集群 | `/k8s` | attack | cluster-admin / node root / 可用云身份 | `/cloud-recon` `/post` `/privesc-linux` `/creds` |
| CI/CD 与供应链 | `/cicd` | attack | runner shell / 部署控制 / 真实云身份 | `/cloud-recon` `/privesc-linux` `/privesc-win` `/post` |
| 钓鱼与客户端攻击 | `/phishing` | attack | host shell 或等效会话 | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| Windows 提权 | `/privesc-win` | attack | Administrator High IL 或 SYSTEM | `/creds` `/post` `/ad-recon` `/tunnel` |
| Linux 提权 | `/privesc-linux` | attack | uid=0 root shell | `/creds` `/post` `/k8s` `/cloud-recon` |
| 凭据攻击 | `/creds` | factory | 可用凭据（明文 / NT / cookie / key） | `/ad-recon` `/cloud-recon` `/service-attack` `/privesc-win` `/privesc-linux` `/post` |
| 后渗透与 C2 | `/post` | post | 所选目标已验证（回连 / persist / loot / 清） | `/tunnel` `/creds` `/ad-recon` `/cloud-recon` |
| shell 稳定化 | `/shell` | support | 可操作会话 | `/privesc-win` `/privesc-linux` `/creds` `/post` |
| 内网穿透 | `/tunnel` | support | 指定网段 / 端口真的通 | `/recon` `/service-attack` `/ad-recon` |
| 端点防御绕过 | `/edr-bypass` | interceptor | 被拦动作可执行 | 回原模块（不给新候选） |






