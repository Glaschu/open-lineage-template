# Dataset YAML Reference

Datasets represent data containers like tables, files, topics, or any storage location.

## Basic Structure

```yaml
version: 1
kind: dataset
namespace: <system-uri>
name: <dataset-name>
```

## Full Enterprise Example

```yaml
version: 1
kind: dataset
id: raw_users                    # Optional, defaults to filename
namespace: postgres://prod-db    # Required: System identifier
name: users                      # Required: Dataset name

description: Raw user data from production database
environment: production

system:
  name: source-db-prod
  type: postgres

schema:
  fields:
    - name: id
      type: INTEGER
      description: Primary key
    - name: email
      type: STRING
      description: User email address

ownership:
  owners:
    - name: Data Engineering Team
      type: TEAM
      email: data-eng@example.com
      brid: BRID-123456

catalogueReference:
  alationId: "4521"
  catalogueUrl: "https://alation.example.com/table/4521"
  certificationType: "GOLD"

cdeLinks:
  - cdeId: "CDE-9988"
    cdeUrl: "https://cde.example.com/elements/9988"
    mappingType: "EXACT_MATCH"

dataQuality:
  completeness: 0.99
  accuracy: 1.0
  lastChecked: "2023-10-27T09:00:00Z"
  reportUrl: "https://dq.example.com/reports/raw_users"

tags:
  - pii
  - production
```

## Field Reference

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | number | Always `1` |
| `kind` | string | Always `dataset` |
| `namespace` | string | System identifier (URI format) |
| `name` | string | Dataset name within namespace |
| `environment` | string | Environment (e.g., production, dev) |

### Enterprise Metadata

| Field | Type | Description |
|-------|------|-------------|
| `system` | object | System details (name, type) |
| `catalogueReference` | object | Link to data catalogue (Alation) |
| `cdeLinks` | array | Links to Critical Data Elements |
| `dataQuality` | object | DQ scores and report links |
| `ownership` | object | Enhanced ownership (BRID, email) |

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

## Catalogue Reference

Link your dataset to the enterprise data catalogue:

```yaml
catalogueReference:
  alationId: "12345"
  catalogueUrl: "https://..."
  certificationType: "GOLD" # GOLD, SILVER, BRONZE, NONE
```

## CDE Links

Link to Critical Data Elements:

```yaml
cdeLinks:
  - cdeId: "CDE-123"
    cdeName: "Customer ID"
    mappingType: "EXACT_MATCH"
```

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
