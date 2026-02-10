"""Shared test fixtures for OpenLineage YAML Tool tests."""

import json
import shutil
import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def tmp_lineage(tmp_path):
    """Create a temporary lineage folder structure with minimal valid files."""
    root = tmp_path / "lineage"
    (root / "application").mkdir(parents=True)
    (root / "dataset").mkdir(parents=True)
    (root / "jobs").mkdir(parents=True)
    return root


@pytest.fixture
def sample_dataset():
    """Minimal valid dataset definition."""
    return {
        "version": 1,
        "kind": "dataset",
        "id": "test_dataset",
        "namespace": "postgres://localhost:5432",
        "name": "public.test_table",
        "schema": {
            "fields": [
                {"name": "id", "type": "integer", "description": "Primary key"},
                {"name": "email", "type": "varchar(255)"},
            ]
        },
        "ownership": {
            "owners": [
                {"name": "data-team", "type": "TEAM", "email": "team@example.com"}
            ]
        },
    }


@pytest.fixture
def sample_dataset_yaml(sample_dataset):
    """Minimal valid dataset as YAML string."""
    import yaml
    return yaml.dump(sample_dataset, default_flow_style=False)


@pytest.fixture
def sample_job():
    """Minimal valid job definition."""
    return {
        "version": 1,
        "kind": "job",
        "id": "test_etl",
        "namespace": "airflow",
        "name": "test-etl-job",
        "inputs": [{"ref": "test_dataset"}],
        "outputs": [
            {
                "ref": "test_output",
                "columnLineage": {
                    "out_id": [
                        {
                            "inputField": "id",
                            "inputDataset": "test_dataset",
                            "transformation": "IDENTITY",
                            "description": "Direct mapping",
                        }
                    ]
                },
            }
        ],
    }


@pytest.fixture
def sample_output_dataset():
    """Output dataset definition for use with jobs."""
    return {
        "version": 1,
        "kind": "dataset",
        "id": "test_output",
        "namespace": "postgres://target-db:5432",
        "name": "public.test_output",
        "schema": {
            "fields": [
                {"name": "out_id", "type": "integer"},
            ]
        },
    }


@pytest.fixture
def sample_application():
    """Minimal valid application definition."""
    return {
        "version": 1,
        "kind": "application",
        "id": "test_app",
        "name": "Test Application",
        "description": "A test application.",
        "owner": {"team": "Test Team"},
    }


@pytest.fixture
def populated_lineage(tmp_lineage, sample_dataset, sample_output_dataset, sample_job, sample_application):
    """Lineage folder with datasets, a job, and an application written to disk."""
    import yaml

    ds_file = tmp_lineage / "dataset" / "test_dataset.yaml"
    ds_file.write_text(yaml.dump(sample_dataset, default_flow_style=False))

    out_file = tmp_lineage / "dataset" / "test_output.yaml"
    out_file.write_text(yaml.dump(sample_output_dataset, default_flow_style=False))

    job_file = tmp_lineage / "jobs" / "test_etl.yaml"
    job_file.write_text(yaml.dump(sample_job, default_flow_style=False))

    app_file = tmp_lineage / "application" / "test_app.yaml"
    app_file.write_text(yaml.dump(sample_application, default_flow_style=False))

    return tmp_lineage


@pytest.fixture
def schema_dir():
    """Return the path to the schemas directory."""
    return Path(__file__).parent.parent / "schemas"
