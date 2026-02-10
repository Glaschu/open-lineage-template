# Complete Examples

Real-world examples of dataset and job definitions.

---

## Example 1: Simple ETL Pipeline

A basic pipeline that reads from a source table and writes to a destination.

### Source Dataset

**`datasets/raw_users.yaml`**
```yaml
version: 1
kind: dataset
namespace: postgres://prod-db
name: users

schema:
  fields:
    - name: id
      type: INTEGER
    - name: email
      type: STRING
    - name: first_name
      type: STRING
    - name: last_name
      type: STRING
    - name: created_at
      type: TIMESTAMP

ownership:
  owners:
    - name: Backend Team
      type: TEAM
```

### Target Dataset

**`datasets/dim_users.yaml`**
```yaml
version: 1
kind: dataset
namespace: bigquery://analytics
name: dim_users

schema:
  fields:
    - name: user_id
      type: INTEGER
    - name: full_name
      type: STRING
    - name: email_domain
      type: STRING
    - name: account_age_days
      type: INTEGER

ownership:
  owners:
    - name: Analytics Team
      type: TEAM
```

### ETL Job

**`jobs/user_etl.yaml`**
```yaml
version: 1
kind: job
namespace: airflow
name: daily_user_sync

jobType:
  processingType: BATCH
  integration: SPARK

inputs:
  - ref: datasets/raw_users.yaml

outputs:
  - ref: datasets/dim_users.yaml
    columnLineage:
      user_id:
        - inputField: id
          inputDataset: datasets/raw_users.yaml
          transformation: IDENTITY
      full_name:
        - inputField: first_name
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM
        - inputField: last_name
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM
          description: CONCAT(first_name, ' ', last_name)
      email_domain:
        - inputField: email
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM
          description: SPLIT(email, '@')[1]
      account_age_days:
        - inputField: created_at
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM
          description: DATEDIFF(CURRENT_DATE, created_at)
```

---

## Example 2: Multi-Source Join

Joining data from multiple sources.

### Job with Multiple Inputs

**`jobs/order_summary.yaml`**
```yaml
version: 1
kind: job
namespace: dbt
name: order_summary

inputs:
  - ref: datasets/raw_orders.yaml
  - ref: datasets/raw_users.yaml
  - ref: datasets/raw_products.yaml

outputs:
  - ref: datasets/fact_orders.yaml
    columnLineage:
      order_id:
        - inputField: id
          inputDataset: datasets/raw_orders.yaml
          transformation: IDENTITY
      customer_name:
        - inputField: first_name
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM
        - inputField: last_name
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM
          description: JOIN on user_id, CONCAT names
      product_name:
        - inputField: name
          inputDataset: datasets/raw_products.yaml
          transformation: IDENTITY
          description: JOIN on product_id
      total_amount:
        - inputField: quantity
          inputDataset: datasets/raw_orders.yaml
          transformation: TRANSFORM
        - inputField: price
          inputDataset: datasets/raw_products.yaml
          transformation: TRANSFORM
          description: quantity * price
```

---

## Example 3: Aggregation Pipeline

Creating a summary table with aggregations.

**`jobs/daily_metrics.yaml`**
```yaml
version: 1
kind: job
namespace: spark
name: daily_metrics_agg

jobType:
  processingType: BATCH

inputs:
  - ref: datasets/raw_events.yaml

outputs:
  - ref: datasets/daily_metrics.yaml
    columnLineage:
      date:
        - inputField: event_timestamp
          inputDataset: datasets/raw_events.yaml
          transformation: TRANSFORM
          description: DATE(event_timestamp)
      event_count:
        - inputField: event_id
          inputDataset: datasets/raw_events.yaml
          transformation: AGGREGATE
          description: COUNT(*)
      unique_users:
        - inputField: user_id
          inputDataset: datasets/raw_events.yaml
          transformation: AGGREGATE
          description: COUNT(DISTINCT user_id)
      total_revenue:
        - inputField: amount
          inputDataset: datasets/raw_events.yaml
          transformation: AGGREGATE
          description: SUM(amount) WHERE event_type = 'purchase'
```

---

## Example 4: PII Masking

Handling sensitive data with masking.

**`jobs/anonymize_users.yaml`**
```yaml
version: 1
kind: job
namespace: spark
name: anonymize_users

documentation:
  description: Creates anonymized user dataset for analytics

inputs:
  - ref: datasets/raw_users.yaml

outputs:
  - ref: datasets/anon_users.yaml
    columnLineage:
      user_key:
        - inputField: id
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM
          masking: true
          description: SHA256(CONCAT(id, salt))
      email_domain:
        - inputField: email
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM
          masking: true
          description: Extract domain only
      signup_month:
        - inputField: created_at
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM
          description: DATE_TRUNC('month', created_at)
```

---

## Example 5: Streaming Pipeline

Real-time streaming job.

**`jobs/event_processor.yaml`**
```yaml
version: 1
kind: job
namespace: flink
name: event_processor

jobType:
  processingType: STREAMING
  integration: FLINK

documentation:
  description: Real-time event processing pipeline

inputs:
  - ref: datasets/events_topic.yaml

outputs:
  - ref: datasets/processed_events.yaml
    columnLineage:
      event_id:
        - inputField: id
          inputDataset: datasets/events_topic.yaml
          transformation: IDENTITY
      event_type:
        - inputField: type
          inputDataset: datasets/events_topic.yaml
          transformation: IDENTITY
      processed_at:
        - inputField: timestamp
          inputDataset: datasets/events_topic.yaml
          transformation: TRANSFORM
          description: Add processing timestamp
```

---

## File Organization

Recommended folder structure:

```
lineage/
├── datasets/
│   ├── raw/              # Source systems
│   │   ├── raw_users.yaml
│   │   └── raw_orders.yaml
│   ├── staging/          # Intermediate
│   │   └── stg_users.yaml
│   └── mart/             # Final tables
│       ├── dim_users.yaml
│       └── fact_orders.yaml
└── jobs/
    ├── ingestion/        # Source to raw
    ├── transform/        # Raw to staging
    └── mart/             # Staging to mart
```
