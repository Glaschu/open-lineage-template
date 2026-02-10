# Job YAML Reference

Jobs represent data transformations that read from input datasets and write to output datasets.

## Basic Structure

```yaml
version: 1
kind: job
namespace: <orchestrator>
name: <job-name>
inputs:
  - ref: <path-to-dataset>
outputs:
  - ref: <path-to-dataset>
```

## Full Example

```yaml
version: 1
kind: job
id: user_etl                     # Optional, defaults to filename
namespace: airflow               # Required: Orchestrator/system
name: daily_user_sync            # Required: Job name

jobType:
  processingType: BATCH          # BATCH, STREAMING, or SERVICE
  integration: SPARK
  jobType: QUERY

documentation:
  description: |
    Daily ETL job that syncs user data from production 
    database to the analytics warehouse.

inputs:
  - ref: datasets/raw_users.yaml
  - ref: datasets/raw_orders.yaml

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
      order_count:
        - inputField: user_id
          inputDataset: datasets/raw_orders.yaml
          transformation: AGGREGATE
          description: COUNT of orders per user
```

## Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | number | Always `1` |
| `kind` | string | Always `job` |
| `namespace` | string | Orchestrator or system name |
| `name` | string | Job name |
| `inputs` | array | Input dataset references |
| `outputs` | array | Output dataset references |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `jobType` | object | Processing type info |
| `documentation` | object | Description and docs |

---

## Inputs and Outputs

Reference datasets using the `ref` field with relative paths:

```yaml
inputs:
  - ref: datasets/source_table.yaml
  - ref: datasets/lookup_table.yaml

outputs:
  - ref: datasets/target_table.yaml
```

The `ref` path is relative to the root folder.

---

## Job Types

Specify how the job processes data:

```yaml
jobType:
  processingType: BATCH    # Required
  integration: SPARK       # Optional
  jobType: QUERY           # Optional
```

### Processing Types

| Type | Description |
|------|-------------|
| `BATCH` | Scheduled batch processing |
| `STREAMING` | Real-time streaming |
| `SERVICE` | API or service-based |

### Common Integrations

| Integration | Description |
|-------------|-------------|
| `SPARK` | Apache Spark jobs |
| `FLINK` | Apache Flink |
| `AIRFLOW` | Airflow operators |
| `DBT` | dbt models |
| `SQL` | SQL queries |
| `PYTHON` | Python scripts |

---

## Documentation

Add descriptions for your jobs:

```yaml
documentation:
  description: |
    This job performs daily aggregation of user activity.
    
    Steps:
    1. Load raw events from source
    2. Filter to valid users only
    3. Aggregate by user_id
    4. Write to warehouse
  contentType: text/markdown
```

---

## Namespace Conventions

Use the orchestrator or system name:

| System | Namespace |
|--------|-----------|
| Airflow | `airflow` |
| dbt | `dbt` |
| Spark | `spark` |
| Databricks | `databricks` |
| Custom | `mycompany/etl` |

---

## Multiple Outputs

A job can have multiple outputs:

```yaml
outputs:
  - ref: datasets/users_daily.yaml
    columnLineage:
      # ... column mappings
  
  - ref: datasets/users_summary.yaml
    columnLineage:
      # ... different mappings
```

Each output can have its own column lineage definition.
