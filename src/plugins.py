"""
Facet plugin loader for extensibility.

Allows users to define custom facets via the openlineage.yaml config file
or by creating Python modules in the facets/ directory.
"""

import os
import yaml
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


class FacetPlugin:
    """Base class for custom facet plugins."""
    
    def __init__(self, name: str, schema_url: str):
        self.name = name
        self.schema_url = schema_url
    
    def validate(self, data: dict) -> List[str]:
        """Validate facet data. Returns list of error messages."""
        return []
    
    def transform(self, data: dict) -> dict:
        """Transform facet data before adding to event."""
        return data
    
    def to_openlineage(self, data: dict) -> dict:
        """Convert to OpenLineage facet format."""
        return {
            "_producer": self.schema_url,
            "_schemaURL": self.schema_url,
            **self.transform(data)
        }


class FacetRegistry:
    """Registry for managing facet plugins."""
    
    def __init__(self):
        self._dataset_facets: Dict[str, FacetPlugin] = {}
        self._job_facets: Dict[str, FacetPlugin] = {}
        self._run_facets: Dict[str, FacetPlugin] = {}
        self._transformers: Dict[str, Callable] = {}
    
    def register_dataset_facet(self, name: str, plugin: FacetPlugin):
        """Register a custom dataset facet."""
        self._dataset_facets[name] = plugin
    
    def register_job_facet(self, name: str, plugin: FacetPlugin):
        """Register a custom job facet."""
        self._job_facets[name] = plugin
    
    def register_run_facet(self, name: str, plugin: FacetPlugin):
        """Register a custom run facet."""
        self._run_facets[name] = plugin
    
    def register_transformer(self, name: str, fn: Callable):
        """Register a custom field transformer function."""
        self._transformers[name] = fn
    
    def get_dataset_facet(self, name: str) -> Optional[FacetPlugin]:
        return self._dataset_facets.get(name)
    
    def get_job_facet(self, name: str) -> Optional[FacetPlugin]:
        return self._job_facets.get(name)
    
    def get_run_facet(self, name: str) -> Optional[FacetPlugin]:
        return self._run_facets.get(name)
    
    def get_transformer(self, name: str) -> Optional[Callable]:
        return self._transformers.get(name)
    
    def list_all(self) -> dict:
        """List all registered plugins."""
        return {
            "dataset_facets": list(self._dataset_facets.keys()),
            "job_facets": list(self._job_facets.keys()),
            "run_facets": list(self._run_facets.keys()),
            "transformers": list(self._transformers.keys())
        }


# Global registry instance
_registry = FacetRegistry()


def get_registry() -> FacetRegistry:
    """Get the global facet registry."""
    return _registry


def load_config(config_path: Path) -> dict:
    """Load configuration from openlineage.yaml."""
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}


def load_custom_facets_from_config(config: dict):
    """Load custom facets defined in config file."""
    custom_facets = config.get('customFacets', {})
    
    for name, facet_def in custom_facets.items():
        if not facet_def:
            continue
            
        schema = facet_def.get('schema', f'https://openlineage.io/custom/{name}')
        plugin = FacetPlugin(name, schema)
        
        # Register based on facet type or default to dataset
        facet_type = facet_def.get('type', 'dataset')
        if facet_type == 'job':
            _registry.register_job_facet(name, plugin)
        elif facet_type == 'run':
            _registry.register_run_facet(name, plugin)
        else:
            _registry.register_dataset_facet(name, plugin)


def load_plugins_from_directory(facets_dir: Path):
    """Load Python facet plugins from a directory."""
    if not facets_dir.exists():
        return
    
    for file_path in facets_dir.glob('*.py'):
        if file_path.name.startswith('_'):
            continue
        
        # Load the module
        spec = importlib.util.spec_from_file_location(
            file_path.stem, 
            file_path
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for register function
            if hasattr(module, 'register'):
                module.register(_registry)


def init_plugins(root_folder: Path):
    """Initialize all plugins from config and facets directory."""
    root_folder = Path(root_folder)
    
    # Load from config
    config_path = root_folder / 'openlineage.yaml'
    config = load_config(config_path)
    load_custom_facets_from_config(config)
    
    # Load from facets directory relative to root_folder
    facets_dir = root_folder / 'facets'
    load_plugins_from_directory(facets_dir)
    
    # Also load from facets directory at project root (parent of src/)
    project_root = Path(__file__).parent.parent
    project_facets_dir = project_root / 'facets'
    if project_facets_dir != facets_dir.resolve():
        load_plugins_from_directory(project_facets_dir)
    
    return config


# Built-in transformers
def _identity(value: Any) -> Any:
    return value

def _uppercase(value: str) -> str:
    return str(value).upper() if value else value

def _lowercase(value: str) -> str:
    return str(value).lower() if value else value

def _hash_value(value: str) -> str:
    import hashlib
    return hashlib.sha256(str(value).encode()).hexdigest()[:16] if value else value


# Register built-in transformers
_registry.register_transformer('IDENTITY', _identity)
_registry.register_transformer('TRANSFORM', _identity)  # Generic transform
_registry.register_transformer('AGGREGATE', _identity)  # Aggregation
_registry.register_transformer('FILTER', _identity)     # Filter
_registry.register_transformer('UPPERCASE', _uppercase)
_registry.register_transformer('LOWERCASE', _lowercase)
_registry.register_transformer('HASH', _hash_value)
