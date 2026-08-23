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
  🌐 <a href="README.md">简体中文</a> ·
  <a href="README_en.md">English</a>
</p>

<a id="about"></a>
## プロジェクトについて

> **レッドチーム作業を支援します。オペレーターが `/module` でモジュールを選択し、AI は得られた成果を `notes.md` に記録してオペレーターの判断と次モジュールの提案に供します。また、監視リスナーの起動 / sudo / パスワード入力 / Permission denied など、AI 自身では実行できずオペレーターの補助が必要な場面では停止し、オペレーターの完了を待ちます。**

本プロジェクトは **レッドチーム作業 / 演習環境 / HTB** などのシナリオを対象とし、半自動のレッドチーム workflow を提供します。

半自動としているのは、実際のレッドチームでは、有能なペンテスターが現場の状況に応じて判断し次の一手を選ぶ必要があり、kill chain 全体を AI に委ねるべきではないからです。AI は実行すべきでない動作を実行したり、重要な情報を見落としたりする可能性があり、それに伴う責任や結果を負うことはできません。同じ理由から、対象の認可範囲も制限していません。これもまたペンテスターの責任に委ねられるべきものです。

本プロジェクトは大部分の skill モジュール、直近の業務における高成功率の exploitation chain、そして 2025–2026 年の比較的新しい技術経路を統合しており、継続的に更新します。

context を短縮し token を節約するため、本プロジェクトは各モジュールの重要な発見と成果を `notes.md` に記録します。現在のモジュールが終了した時点で、オペレーターが `/clear` により context を消去できます。各モジュールの開始時に `notes.md` のデータを自動で読み込み、作業の継続性を保ちます。また各モジュールの詳細な操作手順は `references` に置き、必要になった時にのみ該当する `references/<file>.md` を読み込みます。

<a id="architecture"></a>
## プロジェクト構成

### 基本構成

18 個のモジュール。各モジュールは `SKILL.md`（基本的な方向を判断）と `references/`（詳細な操作手順）で構成されます。

```text
CLAUDE.md                  # グローバルルール、プロジェクトディレクトリに配置
skills/
├── recon/                     # 汎用的な情報収集
│   ├── SKILL.md
│   └── references/     (11)
├── service-attack/            # サービスの脆弱性利用
│   ├── SKILL.md
│   └── references/     (13)
├── web-recon/                 # Web 攻撃面のマッピング
│   ├── SKILL.md
│   └── references/     (5)
├── web-attack/                # Web 脆弱性利用
│   ├── SKILL.md
│   └── references/     (24)
├── ad-recon/                  # AD 列挙
│   ├── SKILL.md
│   └── references/     (5)
├── ad-attack/                 # AD 攻撃利用
│   ├── SKILL.md
│   └── references/     (9)
├── cloud-recon/               # AWS/Azure/GCP/Alibaba Cloud 列挙
│   ├── SKILL.md
│   └── references/     (7)
├── cloud-attack/              # クラウド制御プレーンの利用
│   ├── SKILL.md
│   └── references/     (9)
├── k8s/                       # コンテナとクラスタ
│   ├── SKILL.md
│   └── references/     (6)
├── cicd/                      # CI/CD とサプライチェーン
│   ├── SKILL.md
│   └── references/     (12)
├── phishing/                  # フィッシングとクライアントサイド攻撃
│   ├── SKILL.md
│   └── references/     (8)
├── privesc-win/               # Windows 権限昇格
│   ├── SKILL.md
│   └── references/     (5)
├── privesc-linux/             # Linux 権限昇格
│   ├── SKILL.md
│   └── references/     (5)
├── creds/                     # 認証情報攻撃
│   ├── SKILL.md
│   └── references/     (7)
├── post/                      # ポストエクスプロイトと C2
│   ├── SKILL.md
│   └── references/     (7)
├── shell/                     # shell の安定化
│   ├── SKILL.md
│   └── references/     (6)
├── tunnel/                    # 内部ネットワークの pivoting
│   ├── SKILL.md
│   └── references/     (7)
├── edr-bypass/                # AV/EDR 回避
│   ├── SKILL.md
│   └── references/     (12)
├── shared/                    # モジュール横断の共有リソース
│   ├── modules.yaml           # モジュールレジストリ
│   ├── cve-enrichment.md      # Skill 全体の脆弱性インテリジェンス入口
│   ├── tools.md               # ツールレジストリ
│   └── wordlists.md           # wordlist のパス
└── bin/
    ├── modules.py             # tail / list / show / check、モジュール制御と締め処理
    └── notes.py               # init / validate、操作記録ファイル notes.md
```
> `references/` には計 158 個の操作ドキュメントがあり、`SKILL.md` の判断に応じて読み込まれ、常駐 context には計上されません。

### モジュール一覧

| シナリオ | エントリ | 種別 | 機能 | 成功条件 | デフォルトの次 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 汎用的な情報収集 | `/recon` | recon | 資産の拡張、ホストとポートの発見、サービスバージョンの識別、読み取り専用の列挙、CVE 候補の評価 | サービスマップ + CVE 候補 | `/web-recon` `/ad-recon` `/service-attack` `/phishing` |
| サービスの脆弱性利用 | `/service-attack` | attack | データベース、ファイル・リモートアクセス、メッセージキュー、DNS、ネットワーク機器や BMC などの exploitation chain | 該当サービスの foothold または shell | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| Web 攻撃面のマッピング | `/web-recon` | recon | フィンガープリント、パスと API の発見、JS/sourcemap、プロキシ・キャッシュ境界、WAF、CMS | Web 攻撃面カード | `/web-attack` |
| Web 脆弱性利用 | `/web-attack` | attack | injection、upload、LFI、SSRF/XXE/SSTI、deserialization、JWT/SAML、smuggling、WAF バイパスなどの exploitation chain | foothold、shell、または同等の OS 実行 | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| ドメイン列挙 | `/ad-recon` | recon | ユーザー・グループ・マシン、ACL/委任、ADCS、LAPS、BloodHound、信頼グラフなどの取得 | ドメイン経路と ACL カード | `/ad-attack` `/creds` |
| ドメイン攻撃利用 | `/ad-attack` | attack | Kerberos、委任、強制認証と relay、ACL 濫用、ADCS ESC 全系統、dMSA、横展開などの攻撃 | DA、同等のドメイン制御、または対象ホストの SYSTEM | `/ad-recon` `/creds` `/post` `/privesc-win` |
| クラウド ID 列挙 | `/cloud-recon` | recon | AWS/Azure/GCP/Alibaba Cloud の ID、IAM、信頼、リソース、メタデータなどの取得 | クラウド ID・権限・信頼・リソースのグラフ | `/cloud-attack` `/k8s` |
| クラウド制御プレーンの利用 | `/cloud-attack` | attack | IAM 権限昇格、なりすまし、クロスアカウント信頼、serverless、クラウドネイティブな永続化 | より高いクラウド ID、アカウント制御、または OS 実行を下ろせる compute | `/cloud-recon` `/k8s` `/post` `/ad-recon` |
| コンテナとクラスタ | `/k8s` | attack | RBAC 濫用、secrets、kubelet/etcd、コンテナエスケープ、クラウド ID の紐付け、クラスタ永続化など | cluster-admin、node root、または使用可能なクラウド ID | `/cloud-recon` `/post` `/privesc-linux` `/creds` |
| CI/CD とサプライチェーン | `/cicd` | attack | Jenkins、GitHub Actions、GitLab/ADO、runner、依存関係混同、registry ポイズニング、OIDC などの利用 | runner shell、デプロイ制御、または独立して使用可能な新規 ID | `/cloud-recon` `/privesc-linux` `/privesc-win` `/post` |
| フィッシングとクライアントサイド攻撃 | `/phishing` | attack | ClickFix/FileFix、AiTM セッション、device code/OAuth、helpdesk ソーシャルエンジニアリング、ファイル配送などの攻撃 | host shell または foothold | `/shell` `/privesc-win` `/privesc-linux` `/creds` `/post` |
| Windows 権限昇格 | `/privesc-win` | attack | Potato 系、トークン特権、サービス/DLL/スケジュールタスク、UAC、カーネル LPE などの手法 | Administrator（High IL）または NT AUTHORITY\SYSTEM | `/creds` `/post` `/ad-recon` `/tunnel` |
| Linux 権限昇格 | `/privesc-linux` | attack | sudo/GTFOBins、polkit、SUID/capabilities、systemd、危険なグループ、カーネル LPE などの手法 | uid=0 root shell | `/creds` `/post` `/k8s` `/cloud-recon` |
| 認証情報攻撃 | `/creds` | factory | secret の発見、オフライン解読、ポリシーに応じた spraying、NetNTLM の捕捉と SMB relay、システム認証情報の収集 | 検証済みの使用可能な認証情報 | `/ad-recon` `/cloud-recon` `/service-attack` `/privesc-win` `/privesc-linux` `/post` |
| ポストエクスプロイトと C2 | `/post` | post | ホストの調査、host-native な永続化、Sliver C2、対象を絞った収集と外部持ち出し、クリーンアップ | 選定した目標が検証済み（コールバック / persist / loot / 復元済み） | `/tunnel` `/creds` `/ad-recon` `/cloud-recon` |
| shell の安定化 | `/shell` | support | コールバックの誘導、Linux PTY、Windows ConPTY、リスナー管理、セッション復旧、ファイル転送 | 操作可能で安定したセッション | `/privesc-win` `/privesc-linux` `/creds` `/post` |
| 内部ネットワークの pivoting | `/tunnel` | support | ligolo-ng、chisel、GOST、ネイティブ転送、Dev Tunnels、multi-hop、代替トランスポート | 対象セグメントへの到達性 | `/recon` `/service-attack` `/ad-recon` |
| AV/EDR 回避 | `/edr-bypass` | interceptor | AV/EDR/AMSI/WDAC/PPL/メモリ/カーネルテレメトリによりブロックされた動作を実行可能にする | ブロックされた動作が実行可能になる | 元のモジュールへ戻る |
> `recon` モジュールは情報収集により攻撃面を確認し、`attack` モジュールは exploitation chain を実行して対応する制御権を取得し、`support` モジュールは攻撃チェーンを進めず現在の shell を安定させるのみです。`factory` 種別は `/creds` のみで認証情報の検証だけを行い、`post` 種別は `/post` のみで締めの作業だけを行い、`interceptor` 種別は `/edr-bypass` のみでブロックされた時にのみ実行し、ブロックを回避したら元のモジュールへ戻って実行を継続します。

<a id="usage"></a>
## 使い方

### 前提依存

- **Kali Linux** — 推奨環境。ツールチェーンはデフォルトで Kali のパスおよび `shared/tools.md` の内容に従ってインストールされます
- **Python 3.x** — `bin/modules.py`、`bin/notes.py` の実行に使用
- **Claude Code** — 本 Skill は Claude Code 向けに設計されており、モジュールは `/slash` コマンドで呼び出します

### ディレクトリ階層

**作業ディレクトリ**
```text
~/ops/<target>/
├── CLAUDE.md                  # 作業ルール
├── notes.md                   # 作業記録
└── scans/  loot/  scripts/    # 作業成果物
```
> 自分で作成しても、AI に自動作成させても構いません。

**ツールディレクトリ**
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
> 詳細は `shared/tools.md` を参照してください。

### インストール

    git clone https://github.com/pale-knight/redteam-skill.git
> 18 個のモジュール、`shared/`、`bin/` を skill のグローバルディレクトリ `~/.claude/skills/` に移動し、`CLAUDE.md` を各プロジェクトディレクトリに配置します。

### 開始

```text
mkdir -p ~/ops/<target> && cd ~/ops/<target>
cp CLAUDE.md ./CLAUDE.md
```
`notes.md` を作成
```text
python ~/.claude/skills/bin/notes.py init
```
単一の作業フロー
```text
オペレーター   /<module>
AI            Read ./notes.md
              SKILL.md を読む
              該当フローに到達した時のみ、対応する references/<file>.md を読む
              本モジュールの成功条件まで進める
              オペレーターの補助が必要な時 → 直ちに停止し、何が必要か説明して返信を待つ
              途中で別の攻撃面を発見 → notes に記録するのみ、モジュールは切り替えない
              ./notes.md に追記
              python ~/.claude/skills/bin/modules.py tail <module>
              候補を 1〜3 件挙げる（notes のどの記録に基づくか明記）→ 停止
オペレーター   現在の状況に応じて経路を選択、または /clear の後 /module で次のモジュールを開始
```

## 連絡先

- **X**: @Evander0L
- **問題報告**: [GitHub Issues](https://github.com/pale-knight/redteam-skill/issues)

## 免責事項

本プロジェクトは、適法なセキュリティ研究、教育、演習環境、HTB、および自身が所有するシステムまたは明確な認可を得た対象へのテストにのみ使用してください。

**認可を得ずに対象へアクセス、スキャン、利用、妨害、またはデータを取得することを固く禁じます。** 利用者は、自身の行為が適用される法令および認可範囲に適合することを自ら確認する必要があります。本プロジェクトの濫用によって生じたいかなる損失または法的責任も、すべて利用者自身が負うものとし、プロジェクトの維持者は一切の責任を負いません。
