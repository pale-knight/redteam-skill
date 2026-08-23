# Messaging — RabbitMQ / Kafka / MQTT / ActiveMQ / NATS

消息系统利用优先围绕：

```text
publish / consume permissions
management/admin API
connector/plugin capability
credential reuse
message-driven code execution consumers
```

“能发消息”本身不是服务器 RCE；但一旦确认目标 consumer 会把该消息作为命令、模板、反序列化对象或自动化输入处理，就继续把这条 message-driven chain 做到真实执行结果。

---

## RabbitMQ

有管理凭据：

```bash
curl -su USER:PASS http://TARGET:15672/api/whoami | jq
curl -su USER:PASS http://TARGET:15672/api/permissions | jq
```

如果操作者选择 publish/consume abuse，可使用明确测试 queue/vhost 验证；若已确认生产 consumer 存在命令/模板/反序列化语义，则可继续发送针对该 consumer 的利用输入并以实际 consumer-side execution 为成功条件。

Admin tag 可能允许用户/permission/policy 管理，但 Erlang cookie、plugin、OS RCE 都不是单凭 RabbitMQ admin 自动成立。

---

## Kafka

```bash
kcat -b TARGET:9092 -L
```

如果 ACL 允许 produce，使用明确测试 topic：

```bash
echo 'service-attack-marker' | kcat -b TARGET:9092 -P -t TEST_TOPIC
```

如果 downstream consumer 会把 topic 内容当模板/命令/反序列化输入，继续沿该 Kafka 入口把链走到 consumer-side execution；不要在中途仅因“代码执行发生在另一个进程”就结束。

Kafka Connect 若暴露 REST 管理接口属于高价值独立攻击面：先枚举 connector/plugin，再按精确插件能力验证，不假设任意 connector 都能RCE。

---

## MQTT

如果匿名/已知凭据允许 publish：

```bash
mosquitto_pub -h TARGET -t 'redteam/test' -m 'service-attack-marker'
```

publish capability 只是 primitive；一旦已知设备/consumer 订阅该 topic 且存在命令/模板/自动化语义，可以继续到真实设备控制或 consumer-side execution。

---

## ActiveMQ / Artemis

先精确版本。CVE-2023-46604 等历史 OpenWire 反序列化/RCE 仍可能出现在遗留环境，但不要根据端口直接发送 exploit。使用 `vulnx/cvemap` 确认版本与 PoC，再用 marker 验证。

---

## NATS

NATS 的高价值点通常是：

```text
unauthenticated publish/subscribe
JetStream stream/consumer permissions
monitoring endpoint exposure
credential/NKey/JWT leakage
```

使用测试 subject 做 publish/subscribe marker，不碰生产 wildcard subject。
