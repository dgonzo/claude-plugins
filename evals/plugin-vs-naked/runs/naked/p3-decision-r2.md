# Recommendation: SNS FIFO → three SQS FIFO queues

**Pick SNS + SQS.** Your load is modest, you need per-customer ordering and no data loss, and you have a small team on AWS. SNS + SQS covers all of that with nothing to operate.

## The design

```
order-service ──► SNS FIFO topic "orders"
                     ├──► SQS FIFO "billing"    (+ DLQ)
                     ├──► SQS FIFO "email"      (+ DLQ)
                     └──► SQS FIFO "analytics"  (+ DLQ)
```

- **Per-customer ordering:** set `MessageGroupId = customerId`. Messages for one customer arrive in order. Different customers are processed in parallel, so throughput grows with the number of customers.
- **No lost messages:** SQS stores every message durably across availability zones. A message stays in the queue until the consumer deletes it. Messages that keep failing go to a dead-letter queue (DLQ) after N retries, and you alarm on DLQ depth.
- **Independent consumers:** each service has its own queue. If email is slow or down, billing and analytics are unaffected.
- **Duplicates:** set `MessageDeduplicationId = orderEventId`. This drops duplicate sends from producer retries within a 5-minute window. Consumers should still be idempotent, because delivery is at-least-once end to end.

## Why not the others

**Kafka (MSK)** fits the ordering model well: partition by `customerId`. But 2,000 msg/s is very light for Kafka. You would still have to run brokers, size partitions, manage consumer groups and lag, plan upgrades, and handle retries and DLQs yourself, since Kafka has no built-in DLQ. MSK Serverless reduces the ops work but not the client-side complexity. For a team of 4 that overhead is substantial and buys you little here.

**RabbitMQ (Amazon MQ)** doesn't fit as well:
- Per-key ordering with several competing consumers is awkward. You need the consistent-hash exchange or single-active-consumer workarounds.
- You still manage broker sizing and failover, plus quorum-queue settings for durability.
- It has no advantage over SQS for this workload.

## When I'd change the answer

- **You need replay**, for example rebuilding analytics from 30 days of history or adding new consumers that read from the start. Then use a log: Kinesis Data Streams with partition key `customerId` (still serverless), or MSK if you expect a lot of stream processing. A middle option is to keep SNS/SQS and also send a copy of each message to S3 via Firehose for analytics.
- **You need much higher throughput.** Turn on FIFO high-throughput mode. Check the current per-region SNS FIFO and SQS FIFO limits against your 2k/s peak, because those limits have been raised over time and differ by region. If SNS FIFO is a limit, the order service can publish directly to the three queues instead.

## Gotchas to plan for

1. **The producer side is where messages actually get lost.** If the order service commits to its database and then crashes before publishing, the message is gone, and no broker can prevent that. Use a **transactional outbox**: write the event to an outbox table in the same transaction, then publish from that table. This matters more than which broker you choose.
2. **Head-of-line blocking.** In FIFO, one message that keeps failing stalls that customer's group until it goes to the DLQ. Keep `maxReceiveCount` low, around 3–5, and set visibility timeouts sensibly.
3. **Analytics may not need FIFO.** If it doesn't care about order, give it a standard SQS queue instead. Standard queues are cheaper and have no throughput ceiling.

**Bottom line:** SNS FIFO with SQS FIFO queues, `customerId` as the message group, a DLQ per consumer, an outbox in the order service, and idempotent consumers. Move to Kinesis or MSK only if replay or stream processing becomes a real requirement.
