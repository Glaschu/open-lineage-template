# OpenLineage YAML Tool - Wiki

This wiki explains how to define data lineage using YAML files. Share these docs with any team that needs to document their data pipelines.

## Quick Links

| Document | Description |
|----------|-------------|
| [Quick Start](quick-start.md) | Get started in 5 minutes |
| [Applications](applications.md) | Define logical applications and services. |
| [Datasets](datasets.md) | Define data schemas and origins. |
| [Jobs](jobs.md) | Define transformation logic and lineage. |
| [Column Lineage](column-lineage.md) | Track field-level data flow |
| [Ownership](ownership.md) | Assign data owners |
| [Examples](examples.md) | Complete working examples |

## Overview

This tool uses a simple YAML format to describe:

1. **Datasets** - Tables, files, or any data containers
2. **Jobs** - Processes that read and write data
3. **Column Lineage** - How individual fields flow through jobs

The YAML definitions can be:
- Created manually or via the Lineage Designer UI
- Validated against JSON schemas
- Converted to OpenLineage events for ingestion

## Minimal Example

**Dataset** (`datasets/users.yaml`):
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
```

**Job** (`jobs/sync_users.yaml`):
```yaml
version: 1
kind: job
namespace: airflow
name: sync_users
inputs:
  - ref: datasets/users.yaml
outputs:
  - ref: datasets/users_warehouse.yaml
```

## File Structure

```
lineage/
├── datasets/           # Dataset definitions
│   ├── raw_users.yaml
│   └── processed_users.yaml
└── jobs/               # Job definitions
    └── user_etl.yaml
```

## Need Help?

- Use the [Lineage Designer](../designer/) UI for visual editing
- Check the [examples/](../examples/lineage/) folder for more samples
- Validate YAML with: `python -m src.main validate --root-folder .`
