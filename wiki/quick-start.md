# Quick Start Guide

Get your lineage definitions working in 5 minutes.

## Step 1: Create a Dataset

Create `lineage/datasets/my_table.yaml`:

```yaml
version: 1
kind: dataset
namespace: postgres://my-database
name: my_table
schema:
  fields:
    - name: id
      type: INTEGER
    - name: name
      type: STRING
    - name: created_at
      type: TIMESTAMP
```

**Required fields:**
- `version`: Always `1`
- `kind`: Always `dataset`
- `namespace`: Database or system identifier (URI format)
- `name`: Table or dataset name

## Step 2: Create a Second Dataset

Create `lineage/datasets/my_report.yaml`:

```yaml
version: 1
kind: dataset
namespace: bigquery://analytics
name: my_report
schema:
  fields:
    - name: user_id
      type: INTEGER
    - name: user_name
      type: STRING
```

## Step 3: Create a Job

Create `lineage/jobs/my_etl.yaml`:

```yaml
version: 1
kind: job
namespace: airflow
name: my_etl_job

inputs:
  - ref: datasets/my_table.yaml

outputs:
  - ref: datasets/my_report.yaml
    columnLineage:
      user_id:
        - inputField: id
          inputDataset: datasets/my_table.yaml
          transformation: IDENTITY
      user_name:
        - inputField: name
          inputDataset: datasets/my_table.yaml
          transformation: IDENTITY
```

## Step 4: Validate

```bash
python -m src.main validate --root-folder lineage/
```

## Step 5: Generate Events

```bash
python -m src.main run --root-folder lineage/
```

## Using the Visual Designer

Instead of writing YAML manually:

1. Start the designer: `cd designer && npm run dev`
2. Open http://localhost:5173
3. Create datasets and jobs visually
4. Export to YAML files

## Next Steps

- Read [Datasets](datasets.md) for full schema options
- Read [Jobs](jobs.md) for job configuration
- Read [Column Lineage](column-lineage.md) for field tracking
