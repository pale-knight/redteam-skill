# AWS Serverless 攻击面

## 1. Recon prerequisite

```bash
aws lambda get-function-configuration --function-name <FUNC>
aws lambda get-policy --function-name <FUNC>
aws lambda list-layers
```

记录：Role、Runtime、Handler、Layers、Environment、VPC、URL/trigger。

## 2. UpdateFunctionCode

条件：`lambda:UpdateFunctionCode`。

先备份现有 code location/config；在靶场使用最小验证 payload，例如返回当前 ARN/环境而不是直接长期驻留。

```bash
aws lambda update-function-code \
  --function-name <FUNC> \
  --zip-file fileb://test.zip

aws lambda invoke --function-name <FUNC> out.json
cat out.json
```

验证后恢复原代码/版本。

## 3. UpdateFunctionConfiguration

高价值字段：

```text
Role
Environment
Layers
VPC config
Runtime/Handler
```

`lambda:UpdateFunctionConfiguration` + `iam:PassRole` 可能改变 execution identity。

## 4. Layer / Extension

Lambda Extension 可以通过 Layer 的 `/opt/extensions/` 可执行文件在 execution environment 初始化阶段运行。

条件：可 publish/attach layer 或可更新函数 Layers。

```bash
aws lambda publish-layer-version \
  --layer-name redteam-extension \
  --zip-file fileb://extension.zip
```

保存函数原 Layers：

```bash
aws lambda get-function-configuration --function-name <FUNC> \
  --query 'Layers[].Arn'
```

然后按授权目标把新 Layer ARN 加入 `update-function-configuration --layers ...`。

**Persistence：** 如果 extension/layer 长期附着函数，它属于 cloud-native persistence；回滚必须恢复原 Layers 并删除测试 layer version。

## 5. Function URL

Function URL 需要同时考虑 AuthType 和 resource policy。不要看到 URL 就假设匿名可调用。

```bash
aws lambda get-function-url-config --function-name <FUNC>
aws lambda get-policy --function-name <FUNC>
```

## 6. Success

```text
函数以目标 execution role 运行
→ 可以证明新云身份 / 目标权限
→ 若需要继续云提权：保持 /cloud-attack
→ 若拿到实际 VM/container OS shell：可建议 /post 或 /k8s，由操作者选择
```
