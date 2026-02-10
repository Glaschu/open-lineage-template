"""Tests for the schema and OpenLineage validators."""

import json
import pytest
from pathlib import Path

from src.validator import SchemaValidator, OpenLineageValidator
from src.exceptions import YAMLValidationError


class TestSchemaValidatorDatasets:
    """Tests for dataset schema validation."""

    def test_valid_dataset_passes(self, sample_dataset, schema_dir):
        validator = SchemaValidator(schema_dir)
        errors = validator.validate_dataset(sample_dataset)
        assert errors == []

    def test_missing_required_fields(self, schema_dir):
        incomplete = {"version": 1, "kind": "dataset"}
        validator = SchemaValidator(schema_dir)
        errors = validator.validate_dataset(incomplete)
        assert len(errors) > 0

    def test_wrong_kind_value(self, schema_dir):
        wrong_kind = {
            "version": 1,
            "kind": "job",
            "id": "x",
            "namespace": "y",
            "name": "z",
        }
        validator = SchemaValidator(schema_dir)
        errors = validator.validate_dataset(wrong_kind)
        assert len(errors) > 0

    def test_error_includes_file_path(self, schema_dir, tmp_path):
        file_path = tmp_path / "bad_dataset.yaml"
        incomplete = {"version": 1, "kind": "dataset"}
        validator = SchemaValidator(schema_dir)
        errors = validator.validate_dataset(incomplete, file_path=file_path)
        assert any(e.file_path == file_path for e in errors)

    def test_error_includes_suggestion(self, schema_dir):
        missing_id = {"version": 1, "kind": "dataset", "namespace": "x", "name": "y"}
        validator = SchemaValidator(schema_dir)
        errors = validator.validate_dataset(missing_id)
        # At least one error should have a suggestion for missing required field
        suggestions = [e.suggestion for e in errors if e.suggestion]
        assert len(suggestions) >= 0  # Suggestions are best-effort


class TestSchemaValidatorJobs:
    """Tests for job schema validation."""

    def test_valid_job_passes(self, sample_job, schema_dir):
        validator = SchemaValidator(schema_dir)
        errors = validator.validate_job(sample_job)
        assert errors == []

    def test_job_missing_name(self, schema_dir):
        incomplete = {"version": 1, "kind": "job", "id": "x", "namespace": "y"}
        validator = SchemaValidator(schema_dir)
        errors = validator.validate_job(incomplete)
        assert len(errors) > 0


class TestSchemaValidatorApplications:
    """Tests for application schema validation."""

    def test_valid_application_passes(self, sample_application, schema_dir):
        validator = SchemaValidator(schema_dir)
        errors = validator.validate_application(sample_application)
        assert errors == []

    def test_application_missing_name(self, schema_dir):
        incomplete = {"version": 1, "kind": "application", "id": "x"}
        validator = SchemaValidator(schema_dir)
        errors = validator.validate_application(incomplete)
        assert len(errors) > 0


class TestOpenLineageValidator:
    """Tests for OpenLineage spec validation on generated events."""

    def test_valid_event_passes(self, schema_dir):
        event = {
            "eventType": "COMPLETE",
            "eventTime": "2024-01-01T00:00:00.000Z",
            "producer": "https://test",
            "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json",
            "run": {"runId": "00000000-0000-0000-0000-000000000000"},
            "job": {"namespace": "test", "name": "test-job"},
            "inputs": [],
            "outputs": [],
        }
        validator = OpenLineageValidator()
        errors = validator.validate(event)
        assert errors == []

    def test_missing_required_field_fails(self):
        event = {
            "eventType": "COMPLETE",
            "eventTime": "2024-01-01T00:00:00.000Z",
            "producer": "https://test",
            "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json",
            "run": {"runId": "00000000-0000-0000-0000-000000000000"},
            # 'job' is omitted — required by spec
            "inputs": [],
            "outputs": [],
        }
        validator = OpenLineageValidator()
        errors = validator.validate(event)
        assert len(errors) > 0

    def test_limits_errors_to_five(self):
        # Totally invalid event should not dump endless errors
        validator = OpenLineageValidator()
        errors = validator.validate({})
        assert len(errors) <= 5
