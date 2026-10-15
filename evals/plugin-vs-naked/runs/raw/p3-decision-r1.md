# Recommendation: SNS + SQS (FIFO)

**Use SNS for fan-out to three SQS queues, one per consumer.** Make the topic and queues FIFO, and set `MessageGroupId = customerId`.

```
order-service ──► SNS FIFO topic ──┬──► SQS FIFO: billing   (+ DLQ)
                                   ├──► SQS FIFO: email     (+ DLQ)
                                   └──► SQS FIFO: analytics (+ DLQ)
```

## Why this fits your requirements

| Requirement | How SNS/SQS handles it |
|---|---|
| ~2,000 msg/s peak | Fine. Turn on FIFO high-throughput mode (per-message-group dedup scope) and batch sends. Check the current SNS FIFO and SQS FIFO quotas in your region before you commit. |
| No message loss | SQS stores messages across multiple availability zones. A message is only removed after the consumer deletes it. Messages that keep failing go to a dead-letter queue instead of disappearing. |
| Per-customer ordering | This is exactly what message groups do: order is kept within a group, and different groups are processed in parallel. |
| Three independent consumers | Each consumer gets its own queue. A slow or broken email service doesn't hold up billing. |
| Team of 4 on AWS | Nothing to run: no brokers, no partition rebalancing, no version upgrades. IAM, CloudWatch and Lambda/ECS integration come built in. |

## Why not the others

- **Kafka (MSK):** It's the most capable option, but you'd mostly be paying for features you didn't list: replaying history, many more consumers, stream processing, and very high throughput. For 4 engineers, the cost is ongoing work on partitions, consumer group rebalancing, broker sizing and upgrades. MSK Serverless reduces that work but doesn't remove it. Choose Kafka if you expect to need replay ("rebuild analytics from the last 30 days"), or if the number of consumers will grow a lot.
- **RabbitMQ (Amazon MQ):** It's a good broker but the weakest fit here. You'd still run broker instances, and to avoid losing messages you'd need quorum queues and publisher confirms. Per-customer ordering with parallel consumers requires the consistent-hash exchange plus careful consumer setup. It has no clear advantage over SQS for your case.

## Gotchas to plan for

1. **Publishing must be reliable too.** "Must not be lost" also covers the gap between saving the order to your database and publishing the event. Use a transactional outbox: write the event to an outbox table in the same transaction as the order, then have a relay publish it to SNS. Otherwise a crash at the wrong moment silently drops events, whichever queue you choose.
2. **Make consumers idempotent.** FIFO only deduplicates within a 5-minute window, and redeliveries still happen. Billing in particular should deduplicate on an order or event ID.
3. **A failing message blocks its customer.** In a FIFO group, a message that keeps failing stops later messages for that customer until it reaches the DLQ. Set `maxReceiveCount` and the visibility timeout carefully, and set up alerts on DLQ depth.
4. **Analytics probably doesn't need FIFO.** If analytics doesn't care about order, it can read from a standard queue. Standard queues have higher throughput, cost less, and don't block a customer when one message fails. An SNS FIFO topic can only deliver to FIFO queues, though. To give analytics a standard queue, publish to a standard topic as well, or use EventBridge Pipes or a small forwarder.
5. **Estimate cost with batching.** SQS charges per request. Batch sends, receives and deletes (up to 10 messages each), and use long polling. At a sustained 2,000 msg/s, unbatched costs grow quickly.

## When to revisit

Move to Kafka/MSK if you later need any of these:
- event replay or reprocessing
- many more consumers (5–10+) reading the same stream
- stream processing or joins
- throughput well beyond what FIFO quotas allow

The outbox pattern from point 1 makes that switch fairly easy, because the publishing side of the order service is already isolated.
