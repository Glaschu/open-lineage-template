# Job YAML Reference

Jobs represent data transformations that read from input datasets and write to output datasets.

## Full Enterprise Example

```yaml
version: 1
kind: job
id: user_etl                     # Optional, defaults to filename
name: daily_user_sync            # Required: Job name
jobPath: /etl/users/sync.py
enabled: true

applicationId: data_platform.user_service

execution:
  type: BATCH
  schedule: "0 2 * * *"

extractorMetadata:
  type: manual
  confidence: 1.0
  toolName: Lineage Designer

reviewMetadata:
  lastReviewDate: "2023-10-01"
  lastReviewedByBrid: "BRID-123456"
  reviewStatus: APPROVED

inputs:
  - ref: raw_users

outputs:
  - ref: dim_users
    columnLineage:
      user_id:
        - inputField: id
          inputDataset: raw_users
          transformation: IDENTITY
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

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `applicationId` | string | Reference to parent `Application` |
| `execution` | object | Schedule and type (BATCH/STREAMING) |
| `jobPath` | string | Path to executable code |
| `enabled` | boolean | Whether job is active |

### Enterprise Metadata

| Field | Type | Description |
|-------|------|-------------|
| `extractorMetadata` | object | Tool used to extract lineage |
| `reviewMetadata` | object | Governance review status |
| `ownership` | object | Enhanced ownership (BRID, email) |

---

## Application Link

Link jobs to their parent application for logical grouping:

```yaml
applicationId: <application-id>
```

The application ID must match an existing `Application` entity.

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
