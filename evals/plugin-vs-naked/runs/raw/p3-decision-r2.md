# Pick SNS + SQS, with FIFO, and use customer ID as the ordering key

Your setup is one order service sending the same messages to three consumers, at a moderate rate, with a small team on AWS. SNS + SQS is built for that, and AWS runs it for you.

## Suggested setup

```
Order service ──► SNS FIFO topic ──┬──► SQS FIFO: billing   (+ DLQ)
                                   ├──► SQS FIFO: email     (+ DLQ)
                                   └──► SQS FIFO: analytics (+ DLQ)
```

- **Per-customer ordering:** set `MessageGroupId = customerId`. Messages for the same customer arrive in order. Different customers are processed in parallel, so one slow customer doesn't hold up the others.
- **Not losing messages:** SQS stores messages across several availability zones. Add a dead-letter queue (DLQ) to each consumer queue so failed messages are kept, and alert on DLQ depth.
- **Fan-out:** each consumer has its own queue. A slow or failing analytics consumer never affects billing.
- **Throughput:** 2,000 msg/s fits within SQS FIFO high-throughput mode and SNS FIFO limits in most regions. FIFO quotas have changed over time and differ by region, so check the current numbers for your region before you commit.
- **Operations:** nothing to patch, size or rebalance. For four engineers, this matters more than any other factor here.

## Requirements that apply whichever tool you pick

1. **Make consumers idempotent.** SNS/SQS, Kafka and RabbitMQ all deliver "at least once" in practice, so a message can arrive twice. Billing needs a dedup key, such as an order ID plus event type.
2. **Use a transactional outbox in the order service.** Most lost messages happen between "order saved to the database" and "message published," not inside the broker. Write the event to an outbox table in the same database transaction as the order, then publish from that table.

## Why not the other two

**Kafka (MSK):** Kafka is a strong technology. It handles per-key ordering well, and you can replay old messages and add new consumers later. But 2,000 msg/s is a small load for it, so you'd mostly be paying for capabilities you don't use yet. The cost is broker sizing, partition planning, consumer-group rebalancing, upgrades and a monthly cluster bill. MSK Serverless reduces that work but doesn't remove it. Choose Kafka if any of these apply:
- You need to replay history: rebuild analytics, or backfill a new consumer from months of events. SQS keeps messages for 14 days at most.
- You expect many more consumers, or you plan stream processing (Flink, joins, windowed aggregations).
- Events are becoming the main data backbone of the company.

**RabbitMQ (Amazon MQ):** this is the weakest fit. It handles the throughput, but you'd run it on brokers you have to size. To avoid losing messages you'd need quorum queues and publisher confirms set up correctly. Per-customer ordering across competing consumers also takes extra work, such as the consistent-hash exchange or single-active-consumer. Its routing flexibility doesn't solve any problem you have.

## One adjustment worth considering

Analytics usually doesn't need ordering or per-message processing. You could subscribe **Amazon Data Firehose** directly to the SNS topic and send messages to S3 or your warehouse. That removes one consumer service you'd otherwise have to maintain.

**Bottom line:** use SNS FIFO → SQS FIFO per consumer, grouped by customer ID, with DLQs, idempotent consumers and an outbox. Look at MSK again only if long-term replay or stream processing becomes a real requirement.
