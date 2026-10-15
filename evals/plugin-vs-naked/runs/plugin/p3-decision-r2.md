**I'd pick SNS FIFO fanning out to three SQS FIFO queues, with the customer ID as the message group ID.** It meets all four of your requirements and leaves your team of 4 with no brokers to run.

```
                  ┌──────────────────┐
  Order service ─▶│  SNS FIFO topic  │
   (group ID =    └────────┬─────────┘
    customer ID)           │ fans out to
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
 ┌─────────────┐   ┌─────────────┐   ┌───────────────┐
 │ SQS FIFO    │   │ SQS FIFO    │   │ SQS FIFO      │
 │ billing     │   │ email       │   │ analytics     │
 └──────┬──────┘   └──────┬──────┘   └───────┬───────┘
        ▼ + DLQ           ▼ + DLQ            ▼ + DLQ
```

## How the options compare

| Option | Per-customer ordering | Ops load for 4 engineers | Fit |
|---|---|---|---|
| SNS + SQS FIFO | Native, via message group ID | None, fully managed | Best |
| Kafka on MSK | Native, via partition key | High: partitions, brokers, upgrades | Overbuilt |
| RabbitMQ on Amazon MQ | Weak with competing consumers | Medium: broker sizing and failover | Poor |

## Why SNS and SQS

- **Durability:** SQS stores every message across multiple availability zones. Give each queue a dead-letter queue (DLQ) so failed messages are kept, not dropped.
- **Ordering:** FIFO keeps messages in order within a message group. Using the customer ID as the group ID gives you per-customer order while different customers are processed in parallel.
- **Fan-out:** each consumer has its own queue. A slow analytics consumer can't hold up billing.
- **Load:** 2,000 messages per second is well within FIFO limits when traffic is spread across many customers.

## Why not the other two

**MSK (Kafka)** has one real advantage: you can replay old messages. That matters if analytics needs to reprocess history. The cost is running partitions, consumer groups, broker sizing and version upgrades with four people. If you need replay later, you can add an archive or a Kinesis stream for analytics only. You don't need to move the whole pipeline.

**RabbitMQ** spreads messages across competing consumers, and that breaks per-customer order. The fixes are a consistent-hash exchange or single-active-consumer, and both add work. You would also run the broker yourselves.

## What I checked and what I assumed

I didn't look anything up. The throughput limits come from memory, and AWS has raised them more than once. Before you commit, check the current per-region quotas for:

- SNS FIFO topics, in messages per second
- SQS FIFO high-throughput mode
- each message group, which was about 300 messages per second

The last one matters only if a single customer can produce hundreds of orders per second.

The trade-offs:

- **Duplicates:** FIFO deduplicates only within a 5-minute window. Make each consumer idempotent, keyed on order ID.
- **Blocking:** a message that keeps failing holds up later messages for that customer until it moves to the DLQ. Set `maxReceiveCount` low, around 3 to 5.

The final call is your team's. The question that decides it is whether analytics needs to replay history. If it doesn't, use SNS and SQS. If it does, MSK is worth its ops cost, but only for that consumer.
