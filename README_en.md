<p align="center">
  🌐 <a href="README.md">简体中文</a> ·
  <a href="README_ja.md">日本語</a>
</p>

<a id="about"></a>
## About

> **Assists red team work. The operator picks a module via `/module`; the AI records findings and results in `notes.md` for the operator to review and to suggest the next module, and stops to wait for the operator whenever it cannot act on its own — e.g. listener setup / sudo / password entry / Permission denied.**

This project targets **red team work / labs / HTB** and provides a semi-automated red team workflow.

It is semi-automated by design: in real red team work a competent operator must judge the situation on the ground and choose the next step, rather than handing the whole kill chain to an AI. An AI may execute actions it should not, or miss critical information, and it cannot bear the resulting responsibility or consequences. For the same reason the scope of target authorization is not restricted either — that, too, is the operator's responsibility.

This project integrates the majority of skill modules, high-success-rate exploitation chains from recent engagements, and newer technique paths from 2025–2026, and is updated continuously.

To shorten context and save tokens, this project records each module's key findings and results in `notes.md`; when the current module finishes, the operator can `/clear` the context. At the start of each module `notes.md` is read automatically so work continues seamlessly. Each module's detailed procedures live in `references`, and the corresponding `references/<file>.md` is read only when it is actually needed.

<a id="architecture"></a>
## Architecture

### Basic structure

18 modules. Each module consists of a `SKILL.md` (decides the basic direction) and a `references/` (detailed procedures).

```text
CLAUDE.md                  # Global rules, placed in the project directory
skills/
├── recon/                     # General information gathering
│   ├── SKILL.md
│   └── references/     (11)
├── service-attack/            # Service exploitation
│   ├── SKILL.md
│   └── references/     (13)
├── web-recon/                 # Web attack-surface mapping
│   ├── SKILL.md
│   └── references/     (5)
├── web-attack/                # Web exploitation
│   ├── SKILL.md
│   └── references/     (24)
├── ad-recon/                  # AD enumeration
│   ├── SKILL.md
│   └── references/     (5)
├── ad-attack/                 # AD exploitation
│   ├── SKILL.md
│   └── references/     (9)
├── cloud-recon/               # AWS/Azure/GCP/Alibaba Cloud enumeration
│   ├── SKILL.md
│   └── references/     (7)
├── cloud-attack/              # Cloud control-plane exploitation
│   ├── SKILL.md
│   └── references/     (9)
├── k8s/                       # Containers and clusters
│   ├── SKILL.md
│   └── references/     (6)
├── cicd/                      # CI/CD and supply chain
│   ├── SKILL.md
│   └── references/     (12)
├── phishing/                  # Phishing and client-side attacks
│   ├── SKILL.md
│   └── references/     (8)
├── privesc-win/               # Windows privilege escalation
│   ├── SKILL.md
│   └── references/     (5)
├── privesc-linux/             # Linux privilege escalation
│   ├── SKILL.md
│   └── references/     (5)
├── creds/                     # Credential attacks
│   ├── SKILL.md
│   └── references/     (7)
├── post/                      # Post-exploitation and C2
│   ├── SKILL.md
│   └── references/     (7)
├── shell/                     # Shell stabilization
│   ├── SKILL.md
│   └── references/     (6)
├── tunnel/                    # Internal network pivoting
│   ├── SKILL.md
│   └── references/     (7)
├── edr-bypass/                # AV/EDR evasion
│   ├── SKILL.md
│   └── references/     (12)
├── shared/                    # Cross-module shared resources
│   ├── modules.yaml           # Module registry
│   ├── cve-enrichment.md      # Skill-wide vulnerability intelligence entry
│   ├── tools.md               # Tool registry
│   └── wordlists.md           # Wordlist paths
└── bin/
    ├── modules.py             # tail / list / show / check — module control and wrap-up
    └── notes.py               # init / validate — the notes.md working record
```
> `references/` holds 158 procedure documents in total, loaded as `SKILL.md` decides, and not kept in the resident context.

### Module overview

| Scenario | Entry | Kind | Function | Success condition | Default next |
|:---:|:---:|:---:|:---:|:---:|:---:|
| General information gathering | `/recon` | recon | Asset expansion, host and port discovery, service-version identification, read-only enumeration, CVE candidate assessment | Service map + CVE candidates | `/web-recon` `/ad-recon` `/service-attack` `/phishing` |
| Service exploitation | `/service-attack` | attack | Exploitation chains for databases, file and remote access, message queues, DNS, network devices and BMC, etc. | Foothold or shell on the target service | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| Web attack-surface mapping | `/web-recon` | recon | Fingerprinting, path and API discovery, JS/sourcemap, proxy/cache boundaries, WAF, CMS | Web attack-surface card | `/web-attack` |
| Web exploitation | `/web-attack` | attack | Exploitation chains: injection, upload, LFI, SSRF/XXE/SSTI, deserialization, JWT/SAML, smuggling, WAF bypass | Foothold, shell, or equivalent OS execution | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| Domain enumeration | `/ad-recon` | recon | Users/groups/machines, ACL/delegation, ADCS, LAPS, BloodHound, trust graph, etc. | Domain path and ACL card | `/ad-attack` `/creds` |
| Domain exploitation | `/ad-attack` | attack | Kerberos, delegation, coercion and relay, ACL abuse, full ADCS ESC series, dMSA, lateral movement, etc. | DA, equivalent domain control, or SYSTEM on the target host | `/ad-recon` `/creds` `/post` `/privesc-win` |
| Cloud identity enumeration | `/cloud-recon` | recon | Enumerate identity, IAM, trust, resources, metadata across AWS/Azure/GCP/Alibaba Cloud | Cloud identity, permission, trust, resource graph | `/cloud-attack` `/k8s` |
| Cloud control-plane exploitation | `/cloud-attack` | attack | IAM privesc, impersonation, cross-account trust, serverless, cloud-native persistence | Higher cloud identity, account control, or compute that can deliver OS execution | `/cloud-recon` `/k8s` `/post` `/ad-recon` |
| Containers and clusters | `/k8s` | attack | RBAC abuse, secrets, kubelet/etcd, container escape, cloud-identity binding, cluster persistence, etc. | cluster-admin, node root, or a usable cloud identity | `/cloud-recon` `/post` `/privesc-linux` `/creds` |
| CI/CD and supply chain | `/cicd` | attack | Exploitation of Jenkins, GitHub Actions, GitLab/ADO, runners, dependency confusion, registry poisoning, OIDC, etc. | Runner shell, deployment control, or a new independently usable identity | `/cloud-recon` `/privesc-linux` `/privesc-win` `/post` |
| Phishing and client-side attacks | `/phishing` | attack | ClickFix/FileFix, AiTM sessions, device code/OAuth, helpdesk social engineering, file delivery, etc. | host shell or foothold | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| Windows privilege escalation | `/privesc-win` | attack | Potato family, token privileges, service/DLL/scheduled task, UAC, kernel LPE, etc. | Administrator (High IL) or NT AUTHORITY\SYSTEM | `/creds` `/post` `/ad-recon` `/tunnel` |
| Linux privilege escalation | `/privesc-linux` | attack | sudo/GTFOBins, polkit, SUID/capabilities, systemd, dangerous groups, kernel LPE, etc. | uid=0 root shell | `/creds` `/post` `/k8s` `/cloud-recon` |
| Credential attacks | `/creds` | factory | Secret discovery, offline cracking, policy-aware spraying, NetNTLM capture and SMB relay, system credential harvest | A verified, usable credential | `/ad-recon` `/cloud-recon` `/service-attack` `/privesc-win` `/privesc-linux` `/post` |
| Post-exploitation and C2 | `/post` | post | Host profiling, host-native persistence, Sliver C2, targeted collection and exfil, cleanup | Chosen objective verified (callback / persist / loot / restored) | `/tunnel` `/creds` `/ad-recon` `/cloud-recon` |
| Shell stabilization | `/shell` | support | Callback bootstrapping, Linux PTY, Windows ConPTY, listener management, session recovery, file transfer | A usable, stable session | `/privesc-win` `/privesc-linux` `/creds` `/post` |
| Internal network pivoting | `/tunnel` | support | ligolo-ng, chisel, GOST, native forwarding, Dev Tunnels, multi-hop, fallback transports | Target segment reachable | `/recon` `/service-attack` `/ad-recon` |
| AV/EDR evasion | `/edr-bypass` | interceptor | Turn actions blocked by AV/EDR/AMSI/WDAC/PPL/memory/kernel telemetry into executable ones | Blocked action becomes executable | Return to the origin module |
> `recon` modules gather information to establish the attack surface; `attack` modules run the exploitation chain to obtain the corresponding control; `support` modules do not advance the chain, only stabilize the current shell; the `factory` kind (only `/creds`) merely verifies credentials; the `post` kind (only `/post`) does wrap-up work only; the `interceptor` kind (only `/edr-bypass`) runs only when something is blocked and switches back to the origin module once the block is bypassed.

<a id="usage"></a>
## Usage

### Prerequisites

- **Kali Linux** — recommended environment; the toolchain installs by default along Kali paths and per `shared/tools.md`
- **Python 3.x** — runs `bin/modules.py`, `bin/notes.py`
- **Claude Code** — this Skill is designed for Claude Code; modules are invoked via `/slash` commands

### Directory layout

**Working directory**
```text
~/ops/<target>/
├── CLAUDE.md                  # Working rules
├── notes.md                   # Working record
└── scans/  loot/  scripts/    # Working output
```
> Create them yourself, or let the AI create them automatically.

**Tools directory**
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
> See `shared/tools.md` for details.

### Installation

    git clone https://github.com/pale-knight/redteam-skill.git
> Move the 18 modules, `shared/`, and `bin/` into the global skill directory `~/.claude/skills/`, and place `CLAUDE.md` into each project directory.

### Getting started

```text
mkdir -p ~/ops/<target> && cd ~/ops/<target>
cp CLAUDE.md ./CLAUDE.md
```
Create `notes.md`
```text
python ~/.claude/skills/bin/notes.py init
```
Single workflow
```text
Operator   /<module>
AI         Read ./notes.md
           Read SKILL.md
           Read the matching references/<file>.md only when the flow reaches it
           Work toward this module's success condition
           When operator assistance is needed → stop immediately, state what is needed, wait for reply
           On finding another surface mid-way → only note it, do not switch modules
           Append to ./notes.md
           python ~/.claude/skills/bin/modules.py tail web-attack
           List 1–3 candidates (state which notes records they rest on) → stop
Operator   Choose a path based on the current situation, or /clear then /module to start the next one
```

## Contact

- **X**: @Evander0L
- **Issues**: [GitHub Issues](https://github.com/pale-knight/redteam-skill/issues)

## Disclaimer

This project is intended solely for lawful security research, education, labs, HTB, and testing against your own systems or targets for which you have obtained explicit authorization.

**Accessing, scanning, exploiting, disrupting a target, or extracting data without authorization is strictly prohibited.** Users must ensure their conduct complies with applicable laws, regulations, and the scope of authorization; any loss or legal liability arising from misuse of this project is borne solely by the user, and the maintainer accepts no responsibility.
