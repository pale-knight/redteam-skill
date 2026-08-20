# BloodHound 自定义 Cypher 查询

BloodHound CE的Cypher搜索框中输入。

---

## 高价值目标

```cypher
// 所有Domain Admins
MATCH (u:User)-[:MemberOf*1..]->(g:Group {name:"DOMAIN ADMINS@CORP.COM"}) RETURN u

// 所有Enterprise Admins
MATCH (u:User)-[:MemberOf*1..]->(g:Group {name:"ENTERPRISE ADMINS@CORP.COM"}) RETURN u

// 高权限组的所有成员
MATCH (u)-[:MemberOf*1..]->(g:Group) WHERE g.highvalue=true RETURN u,g
```

## 攻击路径

```cypher
// 从已拥有用户到DA的最短路径
MATCH p=shortestPath((u:User {owned:true})-[*1..]->(g:Group {name:"DOMAIN ADMINS@CORP.COM"})) RETURN p

// 从已拥有计算机到DA
MATCH p=shortestPath((c:Computer {owned:true})-[*1..]->(g:Group {name:"DOMAIN ADMINS@CORP.COM"})) RETURN p

// 所有到DA的路径（限制深度）
MATCH p=allShortestPaths((u)-[*1..5]->(g:Group {name:"DOMAIN ADMINS@CORP.COM"})) WHERE NOT u=g RETURN p
```

## Kerberos攻击面

```cypher
// Kerberoastable用户（有SPN）
MATCH (u:User) WHERE u.hasspn=true RETURN u.name,u.serviceprincipalnames

// AS-REP Roastable用户（不需要预认证）
MATCH (u:User) WHERE u.dontreqpreauth=true RETURN u.name

// Kerberoastable且是高权限
MATCH (u:User)-[:MemberOf*1..]->(g:Group) WHERE u.hasspn=true AND g.highvalue=true RETURN u.name,g.name
```

## 委派

```cypher
// 非约束委派（不含DC）
MATCH (c:Computer {unconstraineddelegation:true}) WHERE NOT c.name STARTS WITH "DC" RETURN c.name

// 约束委派
MATCH (u) WHERE u.allowedtodelegate IS NOT NULL RETURN u.name,u.allowedtodelegate

// RBCD（AllowedToAct边）
MATCH p=(u)-[:AllowedToAct]->(c:Computer) RETURN p
```

## ACL滥用

```cypher
// 谁对DA组有GenericAll/WriteDACL/WriteOwner
MATCH p=(u)-[r:GenericAll|WriteDacl|WriteOwner|Owns]->(g:Group {name:"DOMAIN ADMINS@CORP.COM"}) RETURN p

// 非管理员用户拥有的危险ACL
MATCH p=(u:User)-[r:GenericAll|GenericWrite|WriteDacl|WriteOwner|ForceChangePassword]->(t) WHERE NOT u.admincount=true RETURN p LIMIT 50
```

## 会话和登录

```cypher
// 所有活动会话
MATCH p=(c:Computer)-[:HasSession]->(u:User) RETURN p

// DA在哪台机器上有session
MATCH p=(c:Computer)-[:HasSession]->(u:User)-[:MemberOf*1..]->(g:Group {name:"DOMAIN ADMINS@CORP.COM"}) RETURN p
```

## ADCS

```cypher
// 当前版本中所有ADCSESC*边（避免硬编码旧ESC列表）
MATCH p=()-[r]->()
WHERE type(r) STARTS WITH "ADCSESC"
RETURN p
```

## 清理/实用

```cypher
// 列出所有计算机及其OS
MATCH (c:Computer) RETURN c.name,c.operatingsystem ORDER BY c.name

// 标记所有拥有的节点
MATCH (u {owned:true}) RETURN u.name

// 不活跃用户（>90天未登录）
MATCH (u:User) WHERE u.lastlogon < (datetime().epochSeconds - (90*86400)) RETURN u.name,u.lastlogon
```


## 现代AD辅助查询

```cypher
// Windows Server 2025计算机/DC候选
MATCH (c:Computer)
WHERE c.operatingsystem CONTAINS "2025"
RETURN c.name,c.operatingsystem

// 当前图里指向User/Computer的危险写权限（ResetNightmare/ShadowCred/RBCD等候选）
MATCH p=(u)-[r:GenericAll|GenericWrite|WriteDacl|WriteOwner]->(t)
WHERE t:User OR t:Computer
RETURN p
```

### ADCS注意

BloodHound中的ADCS边会随版本/数据源演进，不假定ESC15/16/17都存在一对一 `ADCSESC<number>` edge。

```
Certipy → 判断模板/CA是否满足ESC15/16/17
BloodHound → 连接Enrollment/ACL/Owned principal/高价值目标攻击路径
```

### OpenGraph

纯AD继续用原生AD图；只有同时需要Entra/MDM/GitHub/其他身份或管理平台关系时再引入OpenGraph。
