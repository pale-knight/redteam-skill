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

18 个模块,每个模块为`SKILL.md`(scope + 分支入口)+ 一个 `references/`(具体打法,走到分支才按需读取,不开局全读)。
整包安装到 `~/.claude/skills/`,全局装一次;作战目录每场行动另建。

​'''text
├── CLAUDE.md                     #全局规则。放进项目目录使用
├── skill/
├── recon/                        #通用信息收集
│   ├── SKILL.md
│   └── references/    (11)      
├── service-attack/               #服务漏洞利用
│   ├── SKILL.md
│   └── references/    (13)       
├── web-recon/                    #Web 攻击面测绘
│   ├── SKILL.md
│   └── references/    (5)       
├── web-attack/                   #Web 漏洞利用
│   ├── SKILL.md
│   └── references/    (24)       
├── ad-recon/                     #域枚举
│   ├── SKILL.md
│   └── references/    (5)        
├── ad-attack/                    #域利用
│   ├── SKILL.md
│   └── references/    (9)       
├── cloud-recon/                  #AWS/Azure/GCP/阿里云枚举
│   ├── SKILL.md
│   └── references/    (7)     
├── cloud-attack/                 #云权限提升与持久化
│   ├── SKILL.md
│   └── references/    (9)        
├── k8s/                          #容器与集群枚举及利用
│   ├── SKILL.md
│   └── references/    (6)       
├── cicd/                         #CI/CD 与供应链枚举及利用
│   ├── SKILL.md
│   └── references/    (12)      
├── phishing/                     #钓鱼和客户端攻击
│   ├── SKILL.md
│   └── references/    (8)       
├── privesc-win/                  #Windows提权
│   ├── SKILL.md
│   └── references/    (5)        
├── privesc-linux/                #Linux提权
│   ├── SKILL.md
│   └── references/    (5)        
├── creds/                        #凭据攻击(只产凭据,不横向)
│   ├── SKILL.md
│   └── references/    (7)        
├── post/                         #后渗透利用与c2
│   ├── SKILL.md
│   └── references/    (7)        
├── shell/                        #shell稳定
│   ├── SKILL.md
│   └── references/    (6)        
├── tunnel/                       #内网端口转发与隧道
│   ├── SKILL.md
│   └── references/    (7)      
├── edr-bypass/                   端点防御绕过(横向拦截器,打完回原模块)
│   ├── SKILL.md
│   └── references/    
├── shared/                       跨模块共享
│   ├── modules.yaml              模块名册:合法模块名 + default_next + never_default
│   ├── cve-enrichment.md         有精确版本时才走的 CVE 富化流程
│   ├── tools.md                  工具安装与代理配置
│   └── wordlists.md              字典位置与选择
│
└── bin/                          辅助脚本
    ├── modules.py                tail / list / show / check —— 收尾时给出候选模块
    └── notes.py                  init / validate —— 作战目录状态文件
​'''

> `references/` 内共 158 份打法文档,按分支懒加载,不计入常驻上下文。








