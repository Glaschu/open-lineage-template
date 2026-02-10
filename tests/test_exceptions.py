"""Tests for custom exception formatting."""

import pytest
from pathlib import Path

from src.exceptions import (
    YAMLParseError,
    YAMLValidationError,
    DatasetReferenceError,
    OpenLineageValidationError,
    APIError,
)


class TestYAMLParseError:
    def test_includes_file_path(self):
        err = YAMLParseError("bad syntax", file_path=Path("/foo/bar.yaml"))
        msg = str(err)
        assert "/foo/bar.yaml" in msg

    def test_includes_line_number(self):
        err = YAMLParseError("bad syntax", file_path=Path("x.yaml"), line=42, column=5)
        msg = str(err)
        assert "Line 42" in msg
        assert "Column 5" in msg

    def test_includes_hint(self):
        err = YAMLParseError("bad syntax")
        msg = str(err)
        assert "Hint" in msg

    def test_header_present(self):
        err = YAMLParseError("bad")
        assert "YAML PARSE ERROR" in str(err)


class TestYAMLValidationError:
    def test_includes_file_and_path(self):
        err = YAMLValidationError(
            "wrong type",
            file_path=Path("dataset.yaml"),
            schema_path="schema.fields[0].type",
        )
        msg = str(err)
        assert "dataset.yaml" in msg
        assert "schema.fields[0].type" in msg

    def test_includes_expected_actual(self):
        err = YAMLValidationError(
            "wrong type",
            expected="type 'string'",
            actual="type 'int'",
        )
        msg = str(err)
        assert "string" in msg
        assert "int" in msg

    def test_includes_suggestion(self):
        err = YAMLValidationError(
            "wrong",
            suggestion="Add 'name: your.dataset.name'",
        )
        msg = str(err)
        assert "Suggestion" in msg


class TestDatasetReferenceError:
    def test_shows_referenced_id(self):
        err = DatasetReferenceError("raw_userz")
        msg = str(err)
        assert "raw_userz" in msg

    def test_shows_available_datasets(self):
        err = DatasetReferenceError(
            "raw_userz",
            available_datasets=["raw_users", "dim_users"],
        )
        msg = str(err)
        assert "raw_users" in msg
        assert "dim_users" in msg

    def test_suggests_similar_name(self):
        err = DatasetReferenceError(
            "raw_user",
            available_datasets=["raw_users", "dim_users"],
        )
        msg = str(err)
        assert "Did you mean" in msg

    def test_shows_job_file(self):
        err = DatasetReferenceError(
            "missing",
            job_file=Path("jobs/etl.yaml"),
        )
        msg = str(err)
        assert "jobs/etl.yaml" in msg

    def test_truncates_long_list(self):
        datasets = [f"dataset_{i}" for i in range(20)]
        err = DatasetReferenceError("missing", available_datasets=datasets)
        msg = str(err)
        assert "... and" in msg


class TestAPIError:
    def test_includes_status_code(self):
        err = APIError("not found", status_code=404, url="https://api.example.com")
        msg = str(err)
        assert "404" in msg
        assert "api.example.com" in msg

    def test_401_suggestion(self):
        err = APIError("unauthorized", status_code=401)
        msg = str(err)
        assert "username and password" in msg

    def test_403_suggestion(self):
        err = APIError("forbidden", status_code=403)
        msg = str(err)
        assert "permission" in msg

    def test_404_suggestion(self):
        err = APIError("not found", status_code=404)
        msg = str(err)
        assert "/api/v1/lineage" in msg

    def test_500_suggestion(self):
        err = APIError("internal error", status_code=500)
        msg = str(err)
        assert "server" in msg.lower()

    def test_truncates_long_response_body(self):
        body = "x" * 1000
        err = APIError("error", response_body=body)
        msg = str(err)
        assert "truncated" in msg

    def test_shows_retry_count(self):
        err = APIError("timeout", retry_count=3)
        msg = str(err)
        assert "3" in msg
