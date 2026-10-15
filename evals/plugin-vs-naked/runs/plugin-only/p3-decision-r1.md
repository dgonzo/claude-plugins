**Pick SNS plus SQS FIFO.** It covers every requirement you listed, and nobody on your team of 4 has to run a broker.

## How it maps to your requirements

```
                ┌──────────────────────────┐
order service ─►│ SNS FIFO topic "orders"  │
                └────────────┬─────────────┘
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
   SQS FIFO billing   SQS FIFO email   SQS FIFO analytics
           │                 │                 │
           ▼                 ▼                 ▼
      billing DLQ        email DLQ      analytics DLQ
```

| Requirement | How SNS + SQS FIFO meets it |
|---|---|
| 2,000 msg/s at peak | SQS FIFO high-throughput mode goes far beyond this |
| No lost messages | Stored across multiple Availability Zones |
| Failed messages kept | A dead-letter queue (DLQ) on each consumer queue |
| Order per customer | Set `MessageGroupId` to the customer ID |
| Duplicates | FIFO removes duplicates within a 5-minute window |
| Three consumers | Each consumer gets its own queue from one topic |
| Operations work | None. AWS fully manages it |

## Why not the other two

| Factor | SNS + SQS | Kafka on MSK | RabbitMQ on Amazon MQ |
|---|---|---|---|
| Ops load for 4 engineers | None | High | Medium |
| Per-customer ordering | Built in | Partition key | Needs extra plugins |
| Replay of old messages | No | Yes | No |
| Cost at 2,000 msg/s | Low | Higher fixed cost | Medium |
| Scaling | Automatic | Partition planning | Broker sizing |

Choose Kafka only if you need to replay history or do stream processing. Neither came up in your requirements. RabbitMQ adds broker management and makes per-customer ordering harder. In return you get nothing on this list.

## Check these before you build

1. **SNS FIFO quota.** SNS FIFO topics have a lower publish quota than SQS. Look up the current limit for your Region in Service Quotas. Use `PublishBatch` to send 10 messages per call. If the quota is still too tight, publish to the three queues directly from the order service.
2. **Publish failures.** The queue cannot save a message the order service never sent. Use a transactional outbox. The order and the outgoing message are written in the same database transaction, and a relay process publishes the message afterwards.
3. **Idempotent consumers.** Duplicate removal only lasts 5 minutes. Billing must still handle the same message twice safely.
4. **Analytics may not need FIFO.** If analytics does not care about order, a standard SQS queue is cheaper and has no throughput ceiling.
