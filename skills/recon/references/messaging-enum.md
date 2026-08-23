# Message Queue / Event Service — 只读枚举

---

## RabbitMQ — 5672 / 15672

```bash
nmap -Pn -sV -p 5672,15672 TARGET
curl -si http://TARGET:15672/
```

有 management API 凭据：

```bash
curl -su USER:PASS http://TARGET:15672/api/overview | jq '.rabbitmq_version,.cluster_name'
curl -su USER:PASS http://TARGET:15672/api/vhosts | jq '.[].name'
curl -su USER:PASS http://TARGET:15672/api/queues | jq '.[]|[.vhost,.name,.messages]'
curl -su USER:PASS http://TARGET:15672/api/exchanges | jq '.[]|[.vhost,.name,.type]'
```

记录 permissions/tags，不创建 queue/user。

---

## Apache Kafka — 9092

```bash
kcat -b TARGET:9092 -L
```

如果返回 metadata，记录：brokers、cluster id、topics、advertised listeners。

有 SASL/TLS 配置时按已有凭据建立只读 metadata connection。

---

## MQTT — 1883 / 8883

```bash
nmap -Pn -sV -p 1883,8883 TARGET
```

允许匿名订阅时可读取少量 `$SYS` 状态：

```bash
mosquitto_sub -h TARGET -p 1883 -t '$SYS/#' -C 20 -v
```

不要默认订阅 `#` 获取业务消息。

---

## NATS — 4222 / 8222

NATS TCP连接常先返回 `INFO {...}`：

```bash
timeout 3 nc TARGET 4222
curl -s http://TARGET:8222/varz | jq 2>/dev/null
curl -s http://TARGET:8222/connz | jq 2>/dev/null
```

记录 auth_required、server id/version、JetStream/monitoring exposure。

---

## ActiveMQ / Artemis — 61616 / 8161 / 61613

```bash
nmap -Pn -sV -p 61616,8161,61613 TARGET
curl -si http://TARGET:8161/
```

记录 OpenWire/STOMP/AMQP 监听与管理控制台版本；CVE 只进入候选研判，不在 Recon 发反序列化 payload。
