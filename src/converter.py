"""
Converter module for transforming YAML definitions to OpenLineage events.

Generates proper OpenLineage RunEvents with all required fields and facets.
"""


import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from .loader import LineageLoader
from .plugins import get_registry, init_plugins
from .exceptions import DatasetReferenceError


# OpenLineage facet schema URLs
FACET_SCHEMA_URLS = {
    "schema": "https://openlineage.io/spec/facets/1-1-1/SchemaDatasetFacet.json",
    "columnLineage": "https://openlineage.io/spec/facets/1-2-0/ColumnLineageDatasetFacet.json",
    "ownership": "https://openlineage.io/spec/facets/1-0-1/OwnershipDatasetFacet.json",
    "dataSource": "https://openlineage.io/spec/facets/1-0-1/DataSourceDatasetFacet.json",
    "jobType": "https://openlineage.io/spec/facets/2-0-2/JobTypeJobFacet.json",
    "documentation": "https://openlineage.io/spec/facets/1-0-1/DocumentationJobFacet.json",
    "parent": "https://openlineage.io/spec/facets/1-0-1/ParentRunFacet.json",
}

# Default producer URL - can be overridden
DEFAULT_PRODUCER = "https://github.com/openlineage-yaml-tool/v1.0.0"
OPENLINEAGE_SCHEMA_URL = "https://openlineage.io/spec/2-0-2/OpenLineage.json"


class OpenLineageConverter:
    """Converts YAML lineage definitions to OpenLineage events."""
    
    def __init__(
        self,
        loader: LineageLoader,
        producer: Optional[str] = None,
        event_time: Optional[datetime] = None
    ):
        """
        Initialize the converter.
        
        Args:
            loader: LineageLoader with datasets and jobs already loaded
            producer: Optional producer URL (uses default if not specified)
            event_time: Optional event time (uses current time if not specified)
        """
        self.loader = loader
        self.producer = producer or DEFAULT_PRODUCER
        self.event_time = event_time
        
        # Initialize plugins
        init_plugins(loader.root_folder)
        self.registry = get_registry()
    
    def convert_all(self) -> List[dict]:
        """
        Convert all loaded jobs to OpenLineage events.
        
        Returns:
            List of OpenLineage RunEvent dictionaries
        """
        # Use already loaded jobs from loader (assumes load_all was already called)
        events = []
        for job_file, job_data in self.loader._jobs:
            event = self.convert_job(job_data, job_file)
            events.append(event)
        
        return events
    
    def convert_job(self, job_data: dict, job_file: Optional[Path] = None) -> dict:
        """
        Convert a single job definition to an OpenLineage RunEvent.
        
        Args:
            job_data: Job definition dictionary
            job_file: Optional source file path for error messages
            
        Returns:
            OpenLineage RunEvent dictionary
        """
        # Generate event time
        event_time = self.event_time or datetime.now(timezone.utc)
        
        # Build the event
        event = {
            "eventType": "COMPLETE",
            "eventTime": event_time.isoformat(),
            "producer": self.producer,
            "schemaURL": OPENLINEAGE_SCHEMA_URL,
            "run": self._build_run(job_data),
            "job": self._build_job(job_data),
            "inputs": self._build_inputs(job_data, job_file),
            "outputs": self._build_outputs(job_data, job_file),
        }
        
        return event
    
    def _build_run(self, job_data: dict) -> dict:
        """Build the run section with a unique runId."""
        run = {
            "runId": str(uuid.uuid4())
        }
        
        facets = {}
        
        # Add parent facet if specified
        if "parent" in job_data:
            facets["parent"] = self._build_facet("parent", {
                "job": {
                    "namespace": job_data["parent"]["namespace"],
                    "name": job_data["parent"]["name"]
                },
                "run": {
                    "runId": str(uuid.uuid4())  # Parent run ID
                }
            })
            
        # Add custom run facets
        for name, plugin in self.registry._run_facets.items():
            if name in job_data:
                errors = plugin.validate(job_data[name])
                if errors:
                    logging.warning(f"Validation errors for run facet {name}: {errors}")
                else:
                    facets[name] = plugin.to_openlineage(job_data[name])
        
        if facets:
            run["facets"] = facets
        
        return run
    
    def _build_job(self, job_data: dict) -> dict:
        """Build the job section with namespace, name, and facets."""
        job = {
            "namespace": job_data.get("namespace", "default"), # robust fallback
            "name": job_data["name"]
        }
        
        facets = {}
        
        # Job type facet
        if "jobType" in job_data:
            facets["jobType"] = self._build_facet("jobType", {
                "processingType": job_data["jobType"].get("processingType", "BATCH"),
                "integration": job_data["jobType"].get("integration", "yaml-tool"),
                "jobType": job_data["jobType"].get("jobType", "TASK"),
            })
        
        # Documentation facet
        if "documentation" in job_data:
            facets["documentation"] = self._build_facet("documentation", {
                "description": job_data["documentation"].get("description", ""),
                "contentType": job_data["documentation"].get("contentType", "text/plain"),
            })
        elif "description" in job_data:
             facets["documentation"] = self._build_facet("documentation", {
                "description": job_data["description"],
                "contentType": "text/plain",
            })
            
        # Application Facet (Logic to resolve applicationId)
        if "applicationId" in job_data and "application" not in job_data:
            app_id = job_data["applicationId"]
            app_data = self.loader.get_application(app_id)
            if app_data:
                # Inject application data into job_data so the plugin can pick it up
                # Or manually use the plugin here. 
                # Let's manually use the plugin if registered, to handle transformation
                app_plugin = self.registry.get_job_facet("application")
                if app_plugin:
                    facets["application"] = app_plugin.to_openlineage(app_data)
        
        # Custom Job Facets (extractorMetadata, reviewMetadata, etc.)
        # Map YAML fields to facet names if they differ, or rely on plugin name matching field name
        # Our example_facets.py uses 'extractor' plugin for 'extractorMetadata' logic? 
        # No, the plugin transform expects the data.
        
        # Check for registered job facets
        for name, plugin in self.registry._job_facets.items():
            # Handle mapping: YAML field might be 'extractorMetadata' but plugin is 'extractor'
            # For now, let's check if the plugin name exists in job_data, OR if there's a convention
            
            # Specific mappings for our known custom facets
            data = None
            if name == "extractor" and "extractorMetadata" in job_data:
                data = job_data["extractorMetadata"]
            elif name == "review" and "reviewMetadata" in job_data:
                data = job_data["reviewMetadata"]
            elif name in job_data:
                data = job_data[name]
                
            if data:
                facets[name] = plugin.to_openlineage(data)
        
        if facets:
            job["facets"] = facets
        
        return job
    
    def _build_inputs(
        self,
        job_data: dict,
        job_file: Optional[Path] = None
    ) -> List[dict]:
        """Build the inputs array by resolving dataset references."""
        inputs = []
        
        for input_ref in job_data.get("inputs", []):
            ref_id = input_ref["ref"]
            dataset = self.loader.resolve_dataset_reference(ref_id, job_file)
            
            input_dataset = {
                "namespace": dataset.get("namespace", "default"),
                "name": dataset["name"],
            }
            
            facets = self._build_dataset_facets(dataset)
            if facets:
                input_dataset["facets"] = facets
            
            inputs.append(input_dataset)
        
        return inputs
    
    def _build_outputs(
        self,
        job_data: dict,
        job_file: Optional[Path] = None
    ) -> List[dict]:
        """Build the outputs array with column lineage."""
        outputs = []
        
        for output_ref in job_data.get("outputs", []):
            ref_id = output_ref["ref"]
            dataset = self.loader.resolve_dataset_reference(ref_id, job_file)
            
            output_dataset = {
                "namespace": dataset.get("namespace", "default"),
                "name": dataset["name"],
            }
            
            # Build dataset facets from the dataset definition
            facets = self._build_dataset_facets(dataset)
            
            # Add column lineage if specified in the job
            if "columnLineage" in output_ref:
                facets["columnLineage"] = self._build_column_lineage(
                    output_ref["columnLineage"],
                    job_file
                )
            
            if facets:
                output_dataset["facets"] = facets
            
            outputs.append(output_dataset)
        
        return outputs
    
    def _build_dataset_facets(self, dataset: dict) -> dict:
        """Build facets from a dataset definition."""
        facets = {}
        
        # Schema facet
        if "schema" in dataset:
            facets["schema"] = self._build_facet("schema", {
                "fields": [
                    {
                        "name": field["name"],
                        "type": field["type"],
                        **({"description": field["description"]} if "description" in field else {})
                    }
                    for field in dataset["schema"].get("fields", [])
                ]
            })
        
        # Ownership facet
        if "ownership" in dataset:
            facets["ownership"] = self._build_facet("ownership", {
                "owners": [
                    {
                        "name": owner["name"],
                        "type": owner.get("type", "PERSON"),
                         **({"email": owner["email"]} if "email" in owner else {})
                    }
                    for owner in dataset["ownership"].get("owners", [])
                ]
            })
        
        # DataSource facet
        if "dataSource" in dataset:
            facets["dataSource"] = self._build_facet("dataSource", {
                "name": dataset["dataSource"].get("name", dataset.get("namespace", "default")),
                "uri": dataset["dataSource"].get("uri", dataset.get("namespace", "default")),
            })
        elif "system" in dataset: # fallback to system for datasource info if not explicit
             facets["dataSource"] = self._build_facet("dataSource", {
                "name": dataset["system"].get("name"),
                "uri": dataset.get("namespace"),
            })
            
        # Custom Dataset Facets
        for name, plugin in self.registry._dataset_facets.items():
            # Specific mappings
            data = None
            if name == "catalogue" and "catalogueReference" in dataset:
                data = dataset["catalogueReference"]
            elif name == "cde" and "cdeLinks" in dataset:
                data = dataset["cdeLinks"]
                # Wrap list if needed, plugin checks for 'cdeLinks' key or raw list
                # Passed as is
            elif name in dataset:
                data = dataset[name]
            
            if data:
                facets[name] = plugin.to_openlineage(data)
        
        return facets
    
    def _build_column_lineage(
        self,
        column_lineage: dict,
        job_file: Optional[Path] = None
    ) -> dict:
        """
        Build the columnLineage facet from job output definition.
        
        Args:
            column_lineage: Column lineage mapping from job YAML
            job_file: Source file for error messages
        """
        fields = {}
        
        for output_field, input_mappings in column_lineage.items():
            input_fields = []
            
            for mapping in input_mappings:
                # Resolve the input dataset to get its namespace/name
                input_dataset = self.loader.resolve_dataset_reference(
                    mapping["inputDataset"],
                    job_file
                )
                
                transformation_type = mapping.get("transformation", "IDENTITY")
                # Map our simplified types to OpenLineage types
                subtype = "IDENTITY" if transformation_type == "IDENTITY" else transformation_type
                
                input_field = {
                    "namespace": input_dataset.get("namespace", "default"),
                    "name": input_dataset["name"],
                    "field": mapping["inputField"],
                    "transformations": [{
                        "type": "DIRECT" if transformation_type == "IDENTITY" else "INDIRECT",
                        "subtype": subtype,
                        "description": mapping.get("description", ""),
                        "masking": mapping.get("masking", False)
                    }]
                }
                input_fields.append(input_field)
            
            fields[output_field] = {
                "inputFields": input_fields
            }
        
        return self._build_facet("columnLineage", {"fields": fields})
    
    def _build_facet(self, facet_type: str, content: dict) -> dict:
        """Build a facet with _producer and _schemaURL."""
        return {
            "_producer": self.producer,
            "_schemaURL": FACET_SCHEMA_URLS.get(facet_type, OPENLINEAGE_SCHEMA_URL),
            **content
        }
