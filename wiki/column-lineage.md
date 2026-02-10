# Column Lineage Reference

Column lineage tracks how individual fields flow from input datasets to output datasets through a job.

## Why Column Lineage?

- **Impact analysis**: Know which reports are affected by a source change
- **Compliance**: Track PII/sensitive data through pipelines
- **Data quality**: Trace errors back to source fields
- **Documentation**: Understand transformations at field level

---

## Basic Structure

Column lineage is defined on each output within a job:

```yaml
outputs:
  - ref: datasets/target.yaml
    columnLineage:
      output_field:
        - inputField: source_field
          inputDataset: datasets/source.yaml
          transformation: IDENTITY
```

---

## Full Example

```yaml
version: 1
kind: job
namespace: spark
name: user_aggregation

inputs:
  - ref: datasets/raw_users.yaml
  - ref: datasets/raw_orders.yaml

outputs:
  - ref: datasets/user_summary.yaml
    columnLineage:
      # Direct copy - no transformation
      user_id:
        - inputField: id
          inputDataset: datasets/raw_users.yaml
          transformation: IDENTITY

      # Concatenation of multiple fields
      full_name:
        - inputField: first_name
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM
          description: CONCAT(first_name, ' ', last_name)
        - inputField: last_name
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM

      # Aggregation from another dataset
      total_orders:
        - inputField: order_id
          inputDataset: datasets/raw_orders.yaml
          transformation: AGGREGATE
          description: COUNT of orders

      # Filtered data
      active_status:
        - inputField: status
          inputDataset: datasets/raw_users.yaml
          transformation: FILTER
          description: WHERE status = 'active'

      # Masked PII field
      email_hash:
        - inputField: email
          inputDataset: datasets/raw_users.yaml
          transformation: TRANSFORM
          masking: true
          description: SHA256 hash of email
```

---

## Transformation Types

| Type | Use When |
|------|----------|
| `IDENTITY` | Direct copy, no changes |
| `TRANSFORM` | Any modification (concat, cast, format) |
| `AGGREGATE` | Aggregations (sum, count, avg) |
| `FILTER` | Filtered subset of data |

### IDENTITY

Use for direct copies with no modification:

```yaml
user_id:
  - inputField: id
    inputDataset: datasets/source.yaml
    transformation: IDENTITY
```

### TRANSFORM

Use for any modification to the data:

```yaml
full_name:
  - inputField: first_name
    inputDataset: datasets/source.yaml
    transformation: TRANSFORM
    description: UPPER(first_name)
```

### AGGREGATE

Use for aggregations:

```yaml
total_amount:
  - inputField: amount
    inputDataset: datasets/orders.yaml
    transformation: AGGREGATE
    description: SUM(amount) GROUP BY user_id
```

### FILTER

Use when applying WHERE conditions:

```yaml
active_users:
  - inputField: user_id
    inputDataset: datasets/users.yaml
    transformation: FILTER
    description: WHERE is_active = true
```

---

## Multiple Sources

A single output field can come from multiple input fields:

```yaml
full_address:
  - inputField: street
    inputDataset: datasets/addresses.yaml
    transformation: TRANSFORM
  - inputField: city
    inputDataset: datasets/addresses.yaml
    transformation: TRANSFORM
  - inputField: country
    inputDataset: datasets/addresses.yaml
    transformation: TRANSFORM
    description: CONCAT(street, ', ', city, ', ', country)
```

---

## Cross-Dataset Lineage

Fields can come from different input datasets:

```yaml
# Output field combining data from two sources
user_with_orders:
  - inputField: name
    inputDataset: datasets/users.yaml
    transformation: IDENTITY
  - inputField: order_count
    inputDataset: datasets/orders.yaml
    transformation: AGGREGATE
    description: JOIN on user_id, COUNT orders
```

---

## Masking Sensitive Data

Mark fields that contain masked/hashed PII:

```yaml
email_hash:
  - inputField: email
    inputDataset: datasets/users.yaml
    transformation: TRANSFORM
    masking: true
    description: SHA256(email)
```

This helps with compliance tracking.

---

## Best Practices

1. **Always add descriptions** for TRANSFORM and AGGREGATE types
2. **Mark masking: true** for any PII transformations
3. **Use IDENTITY** when possible - it's the most specific
4. **Document complex logic** in the description field
5. **Be consistent** with transformation type choices across your team
