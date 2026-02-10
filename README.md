# OpenLineage YAML Tool

Convert declarative YAML lineage definitions to OpenLineage events and send them to an API.

## Features

- **Atomic, reusable definitions**: Define datasets once, reference them in multiple jobs
- **Column-level lineage**: Track field-level transformations between datasets
- **Schema validation**: YAML files are validated before conversion
- **GitLab CI integration**: Include as a component in your pipelines
- **Descriptive errors**: Clear error messages with file paths and line numbers

## Quick Start

### 1. Create your lineage folder structure

```
your-project/
└── lineage/
    ├── datasets/
    │   ├── raw_users.yaml
    │   └── dim_users.yaml
    └── jobs/
        └── users_etl.yaml
```

### 2. Define datasets (`lineage/datasets/raw_users.yaml`)

```yaml
version: 1
kind: dataset
id: raw_users

namespace: "postgres://source-db:5432"
name: "public.raw_users"

schema:
  fields:
    - name: id
      type: integer
    - name: email
      type: varchar(255)

ownership:
  owners:
    - name: data-team
      type: TEAM
```

### 3. Define jobs with references (`lineage/jobs/users_etl.yaml`)

```yaml
version: 1
kind: job
id: users_etl

namespace: data-platform
name: users-etl-job

inputs:
  - ref: raw_users        # References datasets/raw_users.yaml

outputs:
  - ref: dim_users        # References datasets/dim_users.yaml
    columnLineage:
      user_id:
        - inputField: id
          inputDataset: raw_users
          transformation: IDENTITY
      email_hash:
        - inputField: email
          inputDataset: raw_users
          transformation: TRANSFORM
          description: "SHA256 hash for privacy"
          masking: true
```

### 4. Run locally (dry-run)

```bash
# Install dependencies
pip install PyYAML jsonschema requests python-dateutil

# Validate and preview events
python -m src.main --root-folder lineage --dry-run --verbose
```

### 5. Include in GitLab CI

```yaml
include:
  - component: gitlab.com/your-org/open-lineage-template/publish-lineage@main
    inputs:
      root_folder: lineage
      api_url: https://your-openlineage-api.com/api/v1/lineage
      username: $OL_USERNAME
      password: $OL_PASSWORD
```

## CLI Usage

```bash
# Dry run - validate and show events
python -m src.main --root-folder ./lineage --dry-run

# Send to API
python -m src.main --root-folder ./lineage \
    --api-url https://api.example.com/api/v1/lineage \
    --username $OL_USERNAME --password $OL_PASSWORD

# Output to file
python -m src.main --root-folder ./lineage --output events.json
```

### Options

| Flag | Description |
|------|-------------|
| `--root-folder`, `-r` | Path to lineage folder (required) |
| `--api-url`, `-u` | OpenLineage API endpoint |
| `--username` | API username for basic auth |
| `--password` | API password for basic auth |
| `--producer` | Custom producer URL |
| `--dry-run`, `-n` | Validate without sending |
| `--output`, `-o` | Write events to JSON file |
| `--verbose`, `-v` | Verbose output |

## YAML Reference

### Dataset Fields

| Field | Required | Description |
|-------|----------|-------------|
| `version` | Yes | Schema version (always `1`) |
| `kind` | Yes | Must be `dataset` |
| `id` | Yes | Unique identifier for referencing |
| `namespace` | Yes | Data source namespace |
| `name` | Yes | Dataset name (e.g., `schema.table`) |
| `schema.fields` | No | List of field definitions |
| `ownership.owners` | No | List of owners |
| `dataSource` | No | Data source facet |
| `description` | No | Human-readable description |
| `tags` | No | List of tags |

### Job Fields

| Field | Required | Description |
|-------|----------|-------------|
| `version` | Yes | Schema version (always `1`) |
| `kind` | Yes | Must be `job` |
| `id` | Yes | Unique job identifier |
| `namespace` | Yes | Job namespace |
| `name` | Yes | Job name |
| `inputs` | Yes | List of input dataset references |
| `outputs` | Yes | List of output dataset references |
| `outputs[].columnLineage` | No | Column-level lineage mapping |
| `jobType` | No | Job type facet |
| `documentation` | No | Documentation facet |
| `parent` | No | Parent job for hierarchical lineage |

### Column Lineage Transformation Types

| Type | Description |
|------|-------------|
| `IDENTITY` | Direct 1:1 mapping, no transformation |
| `TRANSFORM` | Field is transformed (e.g., hashing, casting) |
| `AGGREGATE` | Field is aggregated from multiple inputs |
| `FILTER` | Field is filtered/subset |

## Error Messages

The tool provides detailed error messages:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ DATASET REFERENCE ERROR                                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

In job file: lineage/jobs/users_etl.yaml
Referenced dataset ID: 'raw_userz'

This dataset ID was not found in the datasets/ folder.

Available datasets:
  - dim_users
  - fact_orders
  - raw_orders
  - raw_users

Did you mean: raw_users?
```

## License

Apache 2.0
