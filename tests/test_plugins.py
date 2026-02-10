"""Tests for the plugin system."""

import pytest
import yaml
from pathlib import Path

from src.plugins import (
    FacetPlugin,
    FacetRegistry,
    load_config,
    load_custom_facets_from_config,
    load_plugins_from_directory,
    get_registry,
)


class TestFacetPlugin:
    """Tests for the base FacetPlugin class."""

    def test_to_openlineage_includes_metadata(self):
        plugin = FacetPlugin("test", "https://test/schema")
        result = plugin.to_openlineage({"key": "value"})

        assert result["_producer"] == "https://test/schema"
        assert result["_schemaURL"] == "https://test/schema"
        assert result["key"] == "value"

    def test_validate_returns_empty_by_default(self):
        plugin = FacetPlugin("test", "https://test/schema")
        assert plugin.validate({"anything": True}) == []

    def test_transform_returns_data_unchanged(self):
        plugin = FacetPlugin("test", "https://test/schema")
        data = {"a": 1, "b": 2}
        assert plugin.transform(data) == data


class TestFacetRegistry:
    """Tests for the FacetRegistry."""

    def test_register_and_get_dataset_facet(self):
        registry = FacetRegistry()
        plugin = FacetPlugin("test_ds", "https://test")
        registry.register_dataset_facet("test_ds", plugin)

        assert registry.get_dataset_facet("test_ds") is plugin
        assert registry.get_dataset_facet("nonexistent") is None

    def test_register_and_get_job_facet(self):
        registry = FacetRegistry()
        plugin = FacetPlugin("test_job", "https://test")
        registry.register_job_facet("test_job", plugin)

        assert registry.get_job_facet("test_job") is plugin

    def test_register_and_get_run_facet(self):
        registry = FacetRegistry()
        plugin = FacetPlugin("test_run", "https://test")
        registry.register_run_facet("test_run", plugin)

        assert registry.get_run_facet("test_run") is plugin

    def test_register_and_get_transformer(self):
        registry = FacetRegistry()
        fn = lambda x: x.upper()  # noqa: E731
        registry.register_transformer("UPPER", fn)

        assert registry.get_transformer("UPPER") is fn

    def test_list_all(self):
        registry = FacetRegistry()
        registry.register_dataset_facet("ds1", FacetPlugin("ds1", ""))
        registry.register_job_facet("job1", FacetPlugin("job1", ""))

        result = registry.list_all()
        assert "ds1" in result["dataset_facets"]
        assert "job1" in result["job_facets"]


class TestConfigLoading:
    """Tests for loading config and custom facets."""

    def test_load_config_returns_empty_on_missing(self, tmp_path):
        result = load_config(tmp_path / "nonexistent.yaml")
        assert result == {}

    def test_load_config_parses_yaml(self, tmp_path):
        config_file = tmp_path / "openlineage.yaml"
        config_file.write_text(yaml.dump({"producer": "https://test"}))

        result = load_config(config_file)
        assert result["producer"] == "https://test"

    def test_load_custom_facets_from_config(self):
        registry = FacetRegistry()
        # Monkey-patch the global registry for this test
        import src.plugins as plugins_module
        original = plugins_module._registry
        plugins_module._registry = registry

        try:
            config = {
                "customFacets": {
                    "quality": {
                        "schema": "https://org.com/quality",
                        "type": "dataset",
                    },
                    "cost": {
                        "schema": "https://org.com/cost",
                        "type": "job",
                    },
                }
            }
            load_custom_facets_from_config(config)

            assert registry.get_dataset_facet("quality") is not None
            assert registry.get_job_facet("cost") is not None
        finally:
            plugins_module._registry = original


class TestPluginDirectoryLoading:
    """Tests for loading plugins from filesystem."""

    def test_loads_plugin_with_register_function(self, tmp_path):
        plugin_code = '''
from src.plugins import FacetPlugin

class MyFacet(FacetPlugin):
    def __init__(self):
        super().__init__("my_custom", "https://test/my_custom")

def register(registry):
    registry.register_dataset_facet("my_custom", MyFacet())
'''
        plugin_file = tmp_path / "my_plugin.py"
        plugin_file.write_text(plugin_code)

        registry = FacetRegistry()
        import src.plugins as plugins_module
        original = plugins_module._registry
        plugins_module._registry = registry

        try:
            load_plugins_from_directory(tmp_path)
            assert registry.get_dataset_facet("my_custom") is not None
        finally:
            plugins_module._registry = original

    def test_skips_underscore_files(self, tmp_path):
        (tmp_path / "_private.py").write_text("raise RuntimeError('should not load')")

        # Should not raise
        load_plugins_from_directory(tmp_path)

    def test_handles_missing_directory(self, tmp_path):
        # Should not raise
        load_plugins_from_directory(tmp_path / "nonexistent")


class TestBuiltInTransformers:
    """Tests for built-in transformer functions."""

    def test_identity_transformer(self):
        registry = get_registry()
        fn = registry.get_transformer("IDENTITY")
        assert fn("hello") == "hello"

    def test_uppercase_transformer(self):
        registry = get_registry()
        fn = registry.get_transformer("UPPERCASE")
        assert fn("hello") == "HELLO"

    def test_lowercase_transformer(self):
        registry = get_registry()
        fn = registry.get_transformer("LOWERCASE")
        assert fn("HELLO") == "hello"

    def test_hash_transformer(self):
        registry = get_registry()
        fn = registry.get_transformer("HASH")
        result = fn("test")
        assert isinstance(result, str)
        assert len(result) == 16  # SHA256 truncated to 16 chars

    def test_hash_handles_none(self):
        registry = get_registry()
        fn = registry.get_transformer("HASH")
        assert fn(None) is None
