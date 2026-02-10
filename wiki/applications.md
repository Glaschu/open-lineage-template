# Application YAML Reference

Applications represent logical groupings of jobs and services.

## Basic Structure

```yaml
version: 1
kind: application
id: <app-id>
name: <app-name>
```

## Full Enterprise Example

```yaml
version: 1
kind: application
id: data_platform.user_service
name: User Data Service
description: Core service for managing user data intake and processing.

owner:
  team: Data Platform Team
  brid: BRID-123456
  email: data-platform@example.com

versions:
  - version: 1.0.0
    releaseDate: 2023-01-01
    changeLog: Initial release

environments:
  - name: production
    url: https://api.users.example.com
    description: Production environment

jobs:
  - ref: users_etl
```

## Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | number | Always `1` |
| `kind` | string | Always `application` |
| `id` | string | Unique identifier |
| `name` | string | Human-readable name |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Detailed description |
| `owner` | object | Ownership details (Team, BRID) |
| `versions` | array | Version history |
| `environments` | array | Deployment environments |
| `jobs` | array | List of associated jobs |

---

## Job Association

There are two ways to associate jobs with an application:

1.  **Inverse Reference (Recommended)**: Define `applicationId` in the **Job** definition.
2.  **Direct Reference**: List jobs in the `jobs` array in the **Application** definition.

**Job Definition:**
```yaml
kind: job
id: users_etl
applicationId: data_platform.user_service
```
