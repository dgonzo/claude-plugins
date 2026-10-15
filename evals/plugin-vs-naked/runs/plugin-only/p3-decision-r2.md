**Pick SNS + SQS FIFO.** It covers all four requirements. Your 4-person team would have no brokers to run.

## How the options compare

| Need | SNS + SQS FIFO | Kafka on MSK | RabbitMQ on Amazon MQ |
|---|---|---|---|
| 2,000 msg/s | Fits with high-throughput mode | Fits easily | Fits on a mid-size broker |
| No message loss | Stored across multiple AZs | Needs replication settings tuned | Needs quorum queues and a cluster |
| Order per customer | Message group ID = customer ID | Partition key = customer ID | Hard to keep with competing consumers |
| Fan-out to 3 consumers | One topic feeds 3 queues | 3 consumer groups | Exchange feeds 3 queues |
| Ops load | None | Partitions, scaling, upgrades | Broker sizing, failover, upgrades |
| Cost at this rate | Lowest | Highest. Brokers run 24/7 | Middle |
| Replay old messages | No | Yes | No |

## Setup

```
                         ┌──► SQS FIFO: billing   ──► DLQ
Order service ──► SNS FIFO ──► SQS FIFO: email     ──► DLQ
  (outbox)        topic  └──► SQS FIFO: analytics ──► DLQ
```

- Set `MessageGroupId` to the customer ID. This keeps per-customer order and still processes different customers in parallel.
- Turn on high-throughput mode for the SNS topic and each queue. Default FIFO limits are below 2,000 msg/s. Check the quota for your region.
- Give each queue a dead-letter queue (DLQ). Failed messages then wait there instead of getting dropped.
- Make consumers idempotent. FIFO deduplication only lasts 5 minutes.
- Use the transactional outbox pattern in the order service. The order row and the event are written in one database transaction. A separate process then publishes the event. Otherwise a crash after the commit but before the publish loses the event, whatever queue you choose.

## When to pick something else

- **Choose MSK** if you need to replay history, expect many more consumers, or plan stream processing. Analytics replaying old events is the usual reason. MSK Serverless reduces the ops load but costs more.
- **Choose RabbitMQ** only if you need complex routing or already run it. Neither is true here.

If analytics does not need ordering, it can read from a standard SQS queue. That gives it more throughput and costs less.
