# 企业级 OSINT / 国内资产拓线

此 reference 只在企业级授权范围需要“从主体扩展资产”时加载；单 IP/HTB 不默认使用。

---

## 1. 组织关系

围绕：

```text
legal entity
subsidiary / acquired brand
historical company name
shared registrar / nameserver / mail infrastructure
shared analytics / tracking IDs
```

结果必须重新确认是否在授权 scope 内。

---

## 2. 中国企业：ICP / 主体 / APP / 小程序

Black-cat 中值得保留的资产发现思路：

```text
企业名
 → 股权/主体关系
 → ICP备案域名
 → APP / 小程序 / 公众号
 → 新域名/API/对象存储
 → DNS/ASN/端口层重新验证
```

工具/数据源可按任务可用性选：

```text
ENScan_GO
工信部ICP备案查询
企业信息数据库
APP商店开发者主体
小程序包静态分析
```

不要把“关联主体”自动等价成“授权目标”。

---

## 3. APP / 小程序静态资产提取

只提取资产/配置线索：

```text
domain / URL / WebSocket
IP
cloud endpoint
API base URL
hard-coded client IDs
non-secret public config
```

敏感凭据如被发现，只记录来源与类型，后续由专门凭据流程处理。

---

## 4. 搜索引擎精确 pivot

常用思路：

```text
certificate serial/fingerprint
favicon hash
body unique string
exact title
same IP + multi-port fingerprint
ICP owner
```

批量结果应去重：

```text
IP:port
hostname
certificate
service family
owner confidence
```
