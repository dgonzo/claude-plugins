**Pick SNS with SQS FIFO queues.** It fits your load, delivery guarantee and per-customer ordering. Your team runs no brokers.

## Design

```
                     ┌──────────────────────────┐
  Order service ───▶ │ SNS FIFO topic "orders"  │
   (outbox table)    │ group ID = customer ID   │
                     └────────────┬─────────────┘
                fans out to       │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
 ┌──────────────┐         ┌──────────────┐          ┌──────────────┐
 │ billing.fifo │         │  email.fifo  │          │analytics.fifo│
 │  + DLQ       │         │  + DLQ       │          │  + DLQ       │
 └──────┬───────┘         └──────┬───────┘          └──────┬───────┘
        ▼                        ▼                         ▼
   Billing consumer        Email consumer          Analytics consumer
```

1. Set the message group ID to the customer ID. SQS FIFO then orders messages within each customer. Different customers still process in parallel.
2. Set the deduplication ID to the order event ID.
3. Give each queue its own dead-letter queue (DLQ). One failing consumer then does not block the other two.
4. Make every consumer idempotent. Retries and redelivery can still repeat a message.
5. Write events through a transactional outbox in the order service. The queue cannot protect a message the service never published. The outbox closes the gap between the database commit and the publish.

## Comparison

| Option | Per-customer ordering | Ops load for 4 engineers | Fit |
|---|---|---|---|
| SNS + SQS FIFO | Message group ID | None, fully managed | Best |
| Kafka on MSK | Partition key | Medium. Serverless MSK is lower | Second |
| RabbitMQ on Amazon MQ | Weak with competing consumers | Medium to high | Last |

Kafka wins only if you need one of these:

- Replay of past events, for example to rebuild analytics.
- Many more consumers planned.
- Stream processing over the event log.

None of these is in your requirements. If replay matters later, add an SNS subscription to Kinesis Data Firehose that writes to S3. That gives you an event archive without running Kafka.

RabbitMQ is last. Your load and guarantees do not need its routing features. Per-key ordering across several consumers is awkward to build on it.

## Check before you commit

You run at 2,000 messages per second, so throughput quotas are the one real risk. I could not check current AWS quotas because web search was denied in this session. What follows is from memory:

- SQS FIFO in high-throughput mode supports far more than 2,000 messages per second per queue. Each message group has a lower cap. One customer will never reach that cap.
- SNS FIFO topics had a lower default quota than SQS. AWS has since added a high-throughput mode for them.

Check the SNS FIFO topic quota for your region on the AWS Service Quotas page. If it is below 2,000 messages per second, request an increase. Otherwise split the topic into several by customer ID hash.
