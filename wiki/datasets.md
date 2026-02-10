# Dataset YAML Reference

Datasets represent data containers like tables, files, topics, or any storage location.

## Basic Structure

```yaml
version: 1
kind: dataset
namespace: <system-uri>
name: <dataset-name>
```

## Full Example

```yaml
version: 1
kind: dataset
id: raw_users                    # Optional, defaults to filename
namespace: postgres://prod-db    # Required: System identifier
name: users                      # Required: Dataset name

description: Raw user data from production database

schema:
  fields:
    - name: id
      type: INTEGER
      description: Primary key
    - name: email
      type: STRING
      description: User email address
    - name: created_at
      type: TIMESTAMP

ownership:
  owners:
    - name: Data Engineering Team
      type: TEAM
    - name: john.smith@company.com
      type: PERSON

tags:
  - pii
  - production

dataSource:
  name: Production PostgreSQL
  uri: jdbc:postgresql://prod-db:5432/main
```

## Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | number | Always `1` |
| `kind` | string | Always `dataset` |
| `namespace` | string | System identifier (URI format) |
| `name` | string | Dataset name within namespace |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (defaults to filename) |
| `description` | string | Human-readable description |
| `schema` | object | Schema definition with fields |
| `ownership` | object | Owner assignments |
| `tags` | array | Tags for categorization |
| `dataSource` | object | Physical data source info |

---

## Schema Fields

Define the structure of your dataset:

```yaml
schema:
  fields:
    - name: column_name
      type: DATA_TYPE
      description: Optional description
```

### Supported Data Types

| Type | Description |
|------|-------------|
| `STRING` | Text/varchar |
| `INTEGER` | Whole numbers |
| `BIGINT` | Large integers |
| `DOUBLE` | Floating point |
| `DECIMAL` | Fixed precision |
| `BOOLEAN` | True/false |
| `DATE` | Date only |
| `TIMESTAMP` | Date and time |
| `ARRAY` | Array type |
| `STRUCT` | Nested structure |
| `BYTES` | Binary data |

---

## Namespace Conventions

Use URI format to identify the system:

| System | Namespace Format | Example |
|--------|------------------|---------|
| PostgreSQL | `postgres://host` | `postgres://prod-db` |
| MySQL | `mysql://host` | `mysql://orders-db` |
| BigQuery | `bigquery://project` | `bigquery://analytics` |
| Snowflake | `snowflake://account` | `snowflake://company` |
| S3 | `s3://bucket` | `s3://data-lake` |
| Kafka | `kafka://cluster` | `kafka://events` |

---

## Ownership

Assign owners to track responsibility:

```yaml
ownership:
  owners:
    - name: Data Team
      type: TEAM
    - name: jane.doe@company.com
      type: PERSON
    - name: etl-service
      type: SERVICE
```

### Owner Types

| Type | Use For |
|------|---------|
| `PERSON` | Individual email addresses |
| `TEAM` | Team or group names |
| `SERVICE` | Service accounts or systems |

---

## Tags

Add searchable tags:

```yaml
tags:
  - pii
  - gdpr
  - production
  - tier1
```

Common tag conventions:
- `pii` - Contains personal data
- `production` / `staging` / `dev` - Environment
- `tier1` / `tier2` - Criticality level
- Domain names like `marketing`, `finance`
