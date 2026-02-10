# Ownership Reference

Define who owns and is responsible for datasets.

## Basic Structure

```yaml
ownership:
  owners:
    - name: Owner Name or Email
      type: PERSON | TEAM | SERVICE
```

---

## Full Example

```yaml
version: 1
kind: dataset
namespace: postgres://prod
name: customers

ownership:
  owners:
    # Team ownership
    - name: Data Engineering
      type: TEAM
    
    # Individual owner
    - name: jane.smith@company.com
      type: PERSON
    
    # Service account (for automated processes)
    - name: etl-service-account
      type: SERVICE
```

---

## Owner Types

| Type | Description | Example |
|------|-------------|---------|
| `PERSON` | Individual person | `john@company.com` |
| `TEAM` | Team or department | `Data Engineering` |
| `SERVICE` | Service account | `airflow-prod` |

---

## Multiple Owners

Datasets can have multiple owners:

```yaml
ownership:
  owners:
    - name: Data Platform Team
      type: TEAM
    - name: alice@company.com
      type: PERSON
    - name: bob@company.com
      type: PERSON
```

---

## Use Cases

### Primary + Backup Owner

```yaml
ownership:
  owners:
    - name: primary-owner@company.com
      type: PERSON
    - name: Data Team
      type: TEAM
```

### Department Ownership

```yaml
ownership:
  owners:
    - name: Finance Department
      type: TEAM
```

### Service Ownership

```yaml
ownership:
  owners:
    - name: payments-service
      type: SERVICE
    - name: Platform Team
      type: TEAM
```

---

## Best Practices

1. **Always assign at least one owner** to every dataset
2. **Use TEAM as backup** - individuals change roles
3. **Use email format** for PERSON type for easy contact
4. **Use SERVICE** for system-generated data

---

## Integration

Ownership data flows to OpenLineage events as the `ownership` facet, enabling:

- Data catalog ownership display
- Access control integration
- Alerting and notification routing
- Compliance audit trails
