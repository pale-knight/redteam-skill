# SAML 认证安全测试详细参考

> 目标：确认 SAMLResponse/Assertion 的**签名验证对象**和应用最终**消费对象**是否一致。拿到管理员身份后继续 Web 管理功能到 Shell；SAML auth bypass 本身不等于服务器 shell。

---

## 1. 识别

常见：

```
SAMLResponse=
RelayState=
/saml/acs
/sso/saml
/Shibboleth.sso/
/consume
/metadata
/idp/metadata
```

Base64 解码：

```
python3 - <<'PY'
import base64,sys
s=sys.stdin.read().strip()
print(base64.b64decode(s+'===').decode(errors='replace'))
PY
```

记录：

```
Response是否签名
Assertion是否签名
NameID
Attribute/Role
Audience
Recipient
InResponseTo
Conditions/NotBefore/NotOnOrAfter
```

---

## 2. 最低成本验证

先做不会伪造签名的 sanity checks：

```
改NameID → 是否被拒
删除Signature → 是否被拒
改Audience → 是否被拒
改Recipient → 是否被拒
重复Assertion → 应用取哪个
```

如果简单改字段就被接受，先处理这个基础缺陷，不必上复杂 XSW。

---

## 3. XML Signature Wrapping (XSW)

核心：

```
签名验证器验证原始/合法 Assertion
应用业务逻辑却读取攻击者插入的另一 Assertion/NameID
```

不同库对节点选择不同，XSW1-XSW8 是常见布局家族，不要只背编号。

### Burp XSW Extension

可用 `d0ge/XSW`：

1. Burp 中捕获认证请求/Response 流程。
2. 右键相关请求 → `WRAP Attack`。
3. 设置想测试的 NameID/ACS/metadata。
4. 比较哪些变体通过认证。

自动生成 payload 后仍要人工确认：

```
是不是新session？
实际登录成谁？
是否只是错误页200？
```

---

## 4. Attribute Pollution

2025 研究显示部分 SAML 栈对重复/污染 attribute 的解析存在差异。

测试思路：

```xml
<Attribute Name="role"><AttributeValue>user</AttributeValue></Attribute>
<Attribute Name="role"><AttributeValue>admin</AttributeValue></Attribute>
```

或同名字段在签名覆盖区和应用消费区出现不同值。

只在你能确认目标使用 SAML attribute 做权限时测试。

---

## 5. Namespace Confusion

XML library / XPath / canonicalization 对 namespace 处理不一致时，可能出现：

```
验证器看到签名节点A
应用通过不同namespace/XPath选择节点B
```

测试时必须保存完整 XML，不能只看浏览器展示，因为 namespace prefix 本身可变。

---

## 6. Void Canonicalization

2025 `The Fragile Lock` 研究提出：某些 Ruby/PHP SAML 生态中，攻击者可让 canonicalization 路径产生错误/空 canonicalized data，同时库仍继续签名验证流程，结合 parser differential 完成认证绕过。

**状态：VERSION/LIBRARY-GATED。**

不要写成“所有 SAML 都能 Void Canonicalization”。先确认：

```
目标SAML库/版本
是否属于公开受影响实现
是否存在对应patch
```

如果有明确 CVE/版本 → 先由 `/web-recon` 做已知 CVE/PoC 验证；没有明确版本、只是手工 parser 差异研究 → 留在本文件。

---

## 7. XXE / XSLT / Transform

SAML 是 XML，部分老库还可能：

```
XXE
XSLT Transform abuse
外部引用
```

XXE → `xxe.md`。

不要因为 XML 中存在 `Transform` 就默认可执行任意 XSLT；必须由目标 XMLDSig 库实际处理。

---

## 8. 成功判断

真正 auth bypass：

```
原本无权限/普通用户
  ↓
篡改SAML
  ↓
服务器生成有效高权限session
  ↓
/me / profile / admin endpoint 确认身份变化
```

只看到 HTTP 302/200 不足。

---

## 9. SAML → Shell

拿到管理员后继续：

```
插件/扩展安装
主题/模板编辑
文件管理器
任务/脚本执行
CI/CD webhook/build
debug/admin console
```

拿 Shell 后 `/web-attack` 结束。
