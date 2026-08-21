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

18 个模块,每个模块 = 一个 `SKILL.md`(scope + 分支入口)+ 一个 `references/`(具体打法,走到分支才按需读取,不开局全读)。
整包安装到 `~/.claude/skills/`,全局装一次;作战目录每场行动另建。

​```text
pale0knight-skill/
│
├── CLAUDE.md                     全局规则。唯一每条消息都进上下文的文件,拷进作战目录使用
├── 使用与工作流.md                安装、单轮执行、全套工作流、常见接错。说明文档,不拷进作战目录
│
├── recon/                        通用信息收集
│   ├── SKILL.md
│   └── references/    (11)       外部拓线 · 主机/端口发现 · 数据库/消息/基础设施等只读服务枚举 · 网络设备 · NSE · CVE 候选
│
├── web-recon/                    Web 攻击面测绘
│   ├── SKILL.md
│   └── references/    (5)        HTTP 拓扑 · 前端资产 · API 发现 · CMS 指纹 · 产品漏洞情报
│
├── web-attack/                   Web 漏洞利用 → 服务器 shell
│   ├── SKILL.md
│   └── references/    (24)       SQLi 四数据库分链 · 命令注入 · 上传 · LFI/RFI · SSRF/XXE/SSTI · XSS · 反序列化(含 Java) · JWT/SAML · API 逻辑 · 请求走私/缓存/解析差异 · WAF 绕过
│
├── ad-recon/                     域内只读枚举
│   ├── SKILL.md
│   └── references/    (5)        BloodHound 查询 · PowerView · 枚举速查 · LAPS 读取 · 域组件漏洞情报
│
├── ad-attack/                    域利用 → DA / 目标主机 SYSTEM
│   ├── SKILL.md
│   └── references/    (9)        Kerberos 攻击 · 委派 · NTLM 强制认证与中继 · 认证反射 · ACL 滥用 · ADCS ESC 全系 · dMSA/BadSuccessor · 身份混淆 · 管理平面 · 横向移动
│
├── cloud-recon/                  云身份与信任图
│   ├── SKILL.md
│   └── references/    (7)        AWS/Azure/GCP/阿里云枚举命令 · IAM 关系图 · 云与 K8s 身份衔接 · 漏洞情报
│
├── cloud-attack/                 云权限提升与持久化
│   ├── SKILL.md
│   └── references/    (9)        四云各自的提权路径与持久化 · AWS Serverless
│
├── k8s/                          容器与集群
│   ├── SKILL.md
│   └── references/    (6)        RBAC 滥用 · 容器逃逸 · 集群持久化 · 绑定云身份 · 工具 · 漏洞情报
│
├── cicd/                         CI/CD 与供应链
│   ├── SKILL.md
│   └── references/    (12)       GitHub Actions · GitLab/Azure DevOps · Jenkins · runner/agent · 工作负载身份 · 依赖与制品供应链 · GitOps/registry · agentic CI/CD · 自动化审计
│
├── service-attack/               非 HTTP 网络服务利用
│   ├── SKILL.md
│   └── references/    (13)       MSSQL/MySQL/Oracle/PostgreSQL/NoSQL · 文件服务 · 消息中间件 · DNS 与网络服务 · 远程访问 · 网络设备及其 CVE · 基础设施
│
├── phishing/                     社工投递
│   ├── SKILL.md
│   └── references/    (8)        AiTM 会话窃取 · device code / OAuth 滥用 · ClickFix/FileFix · 客户端投递 · 协作平台与 helpdesk · 传统客户端 · 战役验证
│
├── privesc-win/                  Windows 本机提权
│   ├── SKILL.md
│   └── references/    (5)        令牌特权 · Potato 家族 · 服务/DLL/计划任务 · 安装程序与 UAC · 内核 LPE
│
├── privesc-linux/                Linux 本机提权
│   ├── SKILL.md
│   └── references/    (5)        sudo/polkit · SUID/capabilities/systemd · GTFOBins · 组与容器 · 内核 LPE
│
├── creds/                        凭据工厂(只产凭据,不横向)
│   ├── SKILL.md
│   └── references/    (7)        Windows 凭据抓取 · 抓包与中继 · 离线破解 · hash 类型判定 · 喷洒与爆破 · 密钥/证书/令牌 · 密钥泄露发现
│
├── post/                         后渗透
│   ├── SKILL.md
│   └── references/    (7)        主机侦察 · Windows/Linux 持久化 · C2(Sliver)与 OPSEC · 收集与外带 · 清理
│
├── shell/                        会话获取与稳定化
│   ├── SKILL.md
│   └── references/    (6)        监听与恢复 · 会话引导 · Linux PTY · Windows ConPTY · 文件传输
│
├── tunnel/                       内网穿透
│   ├── SKILL.md
│   └── references/    (7)        ligolo-ng · chisel/gost · 原生端口转发 · 多跳 · dev tunnels · 备用传输
│
├── edr-bypass/                   端点防御绕过(横向拦截器,打完回原模块)
│   ├── SKILL.md
│   └── references/    (12)       防御面判定 · 静态载荷 · 内存执行 · 进程执行 · 直接系统调用 · 调用栈遥测 · 脚本运行时 · 应用控制 · 内核 EDR · 凭据访问规避 · 验证
│
├── shared/                       跨模块共享
│   ├── modules.yaml              模块名册:合法模块名 + default_next + never_default
│   ├── cve-enrichment.md         有精确版本时才走的 CVE 富化流程
│   ├── tools.md                  工具安装与代理配置
│   └── wordlists.md              字典位置与选择
│
└── bin/                          辅助脚本
    ├── modules.py                tail / list / show / check —— 收尾时给出候选模块
    └── notes.py                  init / validate —— 作战目录状态文件
​```

> `references/` 内共 158 份打法文档,按分支懒加载,不计入常驻上下文。








