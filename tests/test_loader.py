"""Tests for the YAML loader module."""

import yaml
import pytest
from pathlib import Path

from src.loader import LineageLoader
from src.exceptions import YAMLParseError, DatasetReferenceError


class TestFolderStructure:
    """Tests for folder structure validation and creation."""

    def test_creates_missing_subdirectories(self, tmp_path):
        root = tmp_path / "lineage"
        root.mkdir()
        # Don't create subdirs — loader should create them
        loader = LineageLoader(root)
        loader.load_all()

        assert (root / "application").is_dir()
        assert (root / "dataset").is_dir()
        assert (root / "jobs").is_dir()

    def test_raises_on_missing_root(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            loader = LineageLoader(tmp_path / "nonexistent")
            loader.load_all()


class TestLoadDatasets:
    """Tests for dataset loading."""

    def test_loads_valid_dataset(self, tmp_lineage, sample_dataset):
        ds_file = tmp_lineage / "dataset" / "test.yaml"
        ds_file.write_text(yaml.dump(sample_dataset, default_flow_style=False))

        loader = LineageLoader(tmp_lineage)
        apps, datasets, jobs = loader.load_all()

        assert "test_dataset" in datasets
        assert datasets["test_dataset"]["name"] == "public.test_table"

    def test_skips_non_dataset_kind(self, tmp_lineage):
        bad = {"version": 1, "kind": "job", "id": "not_a_dataset", "name": "x"}
        (tmp_lineage / "dataset" / "bad.yaml").write_text(yaml.dump(bad))

        loader = LineageLoader(tmp_lineage)
        _, datasets, _ = loader.load_all()
        assert "not_a_dataset" not in datasets

    def test_raises_on_missing_dataset_id(self, tmp_lineage):
        no_id = {"version": 1, "kind": "dataset", "namespace": "x", "name": "y"}
        (tmp_lineage / "dataset" / "no_id.yaml").write_text(yaml.dump(no_id))

        loader = LineageLoader(tmp_lineage)
        with pytest.raises(YAMLParseError, match="missing required 'id'"):
            loader.load_all()

    def test_warns_on_duplicate_dataset_id(self, tmp_lineage, sample_dataset):
        (tmp_lineage / "dataset" / "a.yaml").write_text(yaml.dump(sample_dataset))
        (tmp_lineage / "dataset" / "b.yaml").write_text(yaml.dump(sample_dataset))

        loader = LineageLoader(tmp_lineage)
        _, datasets, _ = loader.load_all()
        # Should still load but only keep first
        assert "test_dataset" in datasets

    def test_loads_nested_datasets(self, tmp_lineage, sample_dataset):
        nested = tmp_lineage / "dataset" / "subdir"
        nested.mkdir()
        (nested / "deep.yaml").write_text(yaml.dump(sample_dataset))

        loader = LineageLoader(tmp_lineage)
        _, datasets, _ = loader.load_all()
        assert "test_dataset" in datasets

    def test_handles_empty_yaml(self, tmp_lineage):
        (tmp_lineage / "dataset" / "empty.yaml").write_text("")

        loader = LineageLoader(tmp_lineage)
        with pytest.raises(YAMLParseError, match="empty"):
            loader.load_all()

    def test_handles_malformed_yaml(self, tmp_lineage):
        (tmp_lineage / "dataset" / "bad.yaml").write_text("  bad:\n- yaml: [unterminated")

        loader = LineageLoader(tmp_lineage)
        with pytest.raises(YAMLParseError):
            loader.load_all()


class TestLoadJobs:
    """Tests for job loading."""

    def test_loads_valid_job(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        _, _, jobs = loader.load_all()
        assert len(jobs) == 1
        assert jobs[0][1]["id"] == "test_etl"

    def test_skips_non_job_kind(self, tmp_lineage):
        bad = {"version": 1, "kind": "dataset", "id": "x", "name": "y", "namespace": "z"}
        (tmp_lineage / "jobs" / "bad.yaml").write_text(yaml.dump(bad))

        loader = LineageLoader(tmp_lineage)
        _, _, jobs = loader.load_all()
        assert len(jobs) == 0


class TestLoadApplications:
    """Tests for application loading."""

    def test_loads_valid_application(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        apps, _, _ = loader.load_all()
        assert "test_app" in apps

    def test_skips_application_without_id(self, tmp_lineage):
        no_id = {"version": 1, "kind": "application", "name": "No ID App"}
        (tmp_lineage / "application" / "no_id.yaml").write_text(yaml.dump(no_id))

        loader = LineageLoader(tmp_lineage)
        apps, _, _ = loader.load_all()
        assert len(apps) == 0


class TestDatasetReferenceResolution:
    """Tests for resolving dataset references from jobs."""

    def test_resolves_valid_reference(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        ds = loader.resolve_dataset_reference("test_dataset")
        assert ds["name"] == "public.test_table"

    def test_raises_on_unknown_reference(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        with pytest.raises(DatasetReferenceError, match="nonexistent"):
            loader.resolve_dataset_reference("nonexistent")

    def test_error_lists_available_datasets(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()

        with pytest.raises(DatasetReferenceError) as exc_info:
            loader.resolve_dataset_reference("typo_dataset")

        error = exc_info.value
        assert "test_dataset" in error.available_datasets

    def test_get_dataset_ids(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        ids = loader.get_dataset_ids()
        assert "test_dataset" in ids
        assert "test_output" in ids

    def test_get_job_count(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        assert loader.get_job_count() == 1
