# 前端 / JavaScript / Source Map / 历史端点 Recon

> 目标：从已经发现的 Web 应用前端恢复真实 API、隐藏功能、内部主机名、feature flag、源码与历史攻击面。这里只枚举，不在这里测试 SQLi/XSS/SSRF 等漏洞。

---

## 1. 抓取 JavaScript

```
katana -u https://TARGET -d 3 -jc -o katana.txt
```

从 HTML 抽 script：

```
curl -sk https://TARGET/ | grep -Eo 'src=["'"'][^"'"']+\.js[^"'"']*' | cut -d= -f2-
```

下载后统一搜索：

```
mkdir -p js-output
# 将发现的js下载到 js-output/
grep -RniE '/api/|/graphql|/admin|/internal|/debug|/upload|/import|/export|/callback|/webhook' js-output/
grep -RniE 'wss?://|WebSocket\(|socket\.io' js-output/
grep -RniE 'token|secret|apikey|api_key|authorization|bearer|client_secret|password' js-output/
```

压缩 bundle 也可先用 beautifier 后 grep。

### LinkFinder — JS endpoint extraction

对单个 bundle：

```bash
git clone https://github.com/GerbenJavado/LinkFinder.git
cd LinkFinder
pip3 install -r requirements.txt
python3 linkfinder.py -i 'https://TARGET/assets/app.js' -o cli
```

对已经下载的目录：

```bash
python3 linkfinder.py -i '/path/to/js-output/*.js' -r '^/api/' -o results.html
```

LinkFinder 更适合从字符串/相对路径里补 endpoint；Katana 负责 crawl，两者不要互相替代。

---

## 2. Source Map

### 发现

JS 尾部常见：

```
//# sourceMappingURL=app.js.map
```

检查：

```
curl -sk https://TARGET/assets/app.js | tail -n 10
curl -skI https://TARGET/assets/app.js.map
curl -sk https://TARGET/assets/app.js.map -o app.js.map
```

Webpack/Vite 常见 `.map` 还可能从已知 bundle 名直接猜。

### Source Map 高价值字段

JSON 中重点：

```
sources
sourcesContent
names
sourceRoot
```

快速查看源文件列表：

```
python3 - <<'PY'
import json
x=json.load(open('app.js.map'))
for s in x.get('sources',[]): print(s)
PY
```

如果带 `sourcesContent`，直接还原：

```
python3 - <<'PY'
import json, pathlib, re
x=json.load(open('app.js.map'))
out=pathlib.Path('sourcemap-src'); out.mkdir(exist_ok=True)
for i,(name,content) in enumerate(zip(x.get('sources',[]),x.get('sourcesContent',[]))):
    if content is None: continue
    safe=re.sub(r'[^A-Za-z0-9._/-]+','_',name).lstrip('/').replace('../','__/')
    p=out/safe
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content,errors='ignore')
PY
```

然后：

```
grep -RniE '/api/|/graphql|/admin|internal|debug|TODO|FIXME' sourcemap-src/
grep -RniE 'secret|token|api[_-]?key|client[_-]?secret|password|BEGIN .*PRIVATE KEY' sourcemap-src/
```

### 记录而不是直接误报

前端源码出现 `API_KEY` 不等于可用 secret：

```
值是否真实？
是否环境变量占位符？
是否公开型浏览器 key？
是否后端会信任？
```

只记录证据和用途候选。

---

## 3. Framework-specific 前端线索

### Next.js

```
/_next/static/
/_next/data/
__NEXT_DATA__
buildId
/_next/static/chunks/
```

```
curl -sk https://TARGET/ | grep -o '__NEXT_DATA__' -n
```

记录 buildId、route、API base、internal rewrite 线索。

### Vite

常见：

```
/assets/index-<hash>.js
import.meta.env
VITE_*
```

### Webpack

常见：

```
webpackChunk
__webpack_require__
sourceMappingURL
```

---

## 4. 历史 URL

历史数据的目标是找到**当前应用遗忘的旧路径/参数/API**，不是做企业资产拓线。

### Wayback

```
echo target.com | waybackurls | sort -u > wayback.txt
```

### gau

```
echo target.com | gau | sort -u > gau.txt
```

合并：

```
cat wayback.txt gau.txt | sort -u > historical.txt
```

只看参数化 URL：

```
grep '?' historical.txt | sort -u > historical-params.txt
```

高价值名字：

```
grep -Ei '(url=|uri=|file=|path=|redirect=|next=|return=|callback=|webhook=|id=|user=|token=|debug=)' historical-params.txt
```

旧 API：

```
grep -Ei '/api/(v[0-9]+|beta|alpha|legacy|old|internal|private|mobile|partner)/' historical.txt
```

重新探活：

```
cat historical.txt | httpx -silent -sc -cl -location -o historical-live.txt
```

`403/405` 保留，因为端点可能真实存在。

---

## 5. Git / 备份 / 构建产物

`.git`：

```
git-dumper https://TARGET/.git/ ./git-output
cd git-output
git log --oneline --all
git show
```

常见构建/备份：

```
.env
.env.production
.env.local
config.js
settings.js
manifest.json
asset-manifest.json
backup.zip
source.zip
www.zip
app.tar.gz
package-lock.json
yarn.lock
pnpm-lock.yaml
composer.lock
pom.xml
build.gradle
gradle.lockfile
```

锁文件价值：精确依赖版本 → `/web-recon` CVE 查询。

---

## 6. 数据库线索的正确处理

Web 前端/源码可能泄露：

```
mysql://
postgresql://
jdbc:mysql:
jdbc:postgresql:
Server=...;Database=...
mongodb://
redis://
```

这里仅记录：

```
DBMS
hostname
port
username
credential source
是否看起来仅内网可达
```

**不要在 `/web-recon` 里启动 psql/mysql/nxc 等数据库服务枚举。**

如果这些凭据是通过 Web 漏洞/功能获得，之后 `/web-attack` 可将其作为当前 Web 利用链的一部分使用，目标仍是 Shell；如果只是独立服务暴露，则由 `/recon` 路由。
