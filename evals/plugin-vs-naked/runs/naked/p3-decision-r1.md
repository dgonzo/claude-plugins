# Use SNS + SQS (FIFO)

Publish order events to an **SNS FIFO topic** and give each consumer its own **SQS FIFO queue** subscribed to that topic: billing, email and analytics. Set `MessageGroupId = customerId`.

## Why this fits

- **2,000 msg/s:** SQS FIFO handles this easily in high-throughput mode. SNS FIFO topics default to about 300 msg/s, so you must turn on **high-throughput mode** on the topic as well. Check the current limits for your region before you commit.
- **No lost messages:** SQS stores every message across multiple availability zones. Add a dead-letter queue (DLQ) to each queue so failures are kept and visible instead of dropped.
- **Per-customer ordering:** this is what message groups do. Each customer's messages stay in order, and different customers are processed in parallel.
- **Team of 4:** there are no brokers, partitions, upgrades or disk sizing to manage. You get IAM, CloudWatch and Lambda/ECS integration with no extra setup. Of the three options, this one takes the least of your team's time to run.

## Why not the others

- **Kafka (MSK):** strong technically, but too much to operate for 4 people at 2k msg/s. You'd manage partitions, consumer groups, rebalancing and broker sizing. MSK Serverless takes some of that away, but not all. Choose Kafka only if you need **replay** (for example, reprocessing history into analytics) or expect stream processing or 10–100x growth.
- **RabbitMQ (Amazon MQ):** handling ordering per customer is awkward. You'd need the consistent-hash exchange or single active consumers. You'd also be running a broker for no benefit over SQS.

## Things to get right whichever you choose

1. **Use a transactional outbox in the order service.** Messages are most often lost between "order saved to the DB" and "event published", not in the queue. Write the event to an outbox table in the same transaction as the order, then publish from that table.
2. **Make consumers idempotent.** FIFO deduplication only covers a 5-minute window, and redelivery can still happen. Billing in particular must not charge twice, so key it on order ID.
3. **Plan for head-of-line blocking.** If one message keeps failing, that customer's group stops until the message goes to the DLQ. Set `maxReceiveCount` deliberately and alert on DLQ depth.
4. **Analytics may not need ordering.** If it doesn't, its queue can be simpler, but one FIFO setup for all three consumers is fine to start.

**When to choose differently:** if analytics needs to replay past events, add a Kinesis Data Stream or Kafka *alongside* this setup for the analytics side. Keep billing and email on SQS.
