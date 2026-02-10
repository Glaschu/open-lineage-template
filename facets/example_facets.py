"""
Example custom facet plugin.

To create your own facet plugin:
1. Create a Python file in the facets/ directory
2. Define a FacetPlugin subclass
3. Implement the register() function

This file defines enterprise-specific facets for OpenLineage.
"""

from src.plugins import FacetPlugin, FacetRegistry
from typing import List, Dict, Any


class CatalogueFacet(FacetPlugin):
    """Facet for data catalogue metadata (e.g., Alation)."""
    
    def __init__(self):
        super().__init__(
            name="catalogue",
            schema_url="https://github.com/openlineage/OpenLineage/blob/main/spec/facets/CatalogueDatasetFacet.json"
        )
    
    def validate(self, data: dict) -> List[str]:
        return [] # Simplified validation
    
    def transform(self, data: dict) -> dict:
        return {
            "alationId": data.get("alationId"),
            "catalogueUrl": data.get("catalogueUrl"),
            "certificationType": data.get("certificationType")
        }


class CDEFacet(FacetPlugin):
    """Facet for Critical Data Element (CDE) links."""
    
    def __init__(self):
        super().__init__(
            name="cde",
            schema_url="https://github.com/openlineage/OpenLineage/blob/main/spec/facets/CDEDatasetFacet.json"
        )
    
    def validate(self, data: dict) -> List[str]:
        return []
    
    def transform(self, data: dict) -> dict:
        # Expecting a list of CDE links in the 'cdeLinks' field of the dataset
        if "cdeLinks" in data:
            return {"cdeLinks": data["cdeLinks"]}
        return {"cdeLinks": data} # fallback if passed directly


class SystemFacet(FacetPlugin):
    """Facet for system information."""
    
    def __init__(self):
        super().__init__(
            name="system",
            schema_url="https://github.com/openlineage/OpenLineage/blob/main/spec/facets/SystemDatasetFacet.json"
        )
    
    def validate(self, data: dict) -> List[str]:
        return []
    
    def transform(self, data: dict) -> dict:
        return {
            "name": data.get("name"),
            "type": data.get("type"),
            "description": data.get("description")
        }


class ApplicationFacet(FacetPlugin):
    """Facet for Application metadata linked to a Job."""
    
    def __init__(self):
        super().__init__(
            name="application",
            schema_url="https://github.com/openlineage/OpenLineage/blob/main/spec/facets/ApplicationJobFacet.json"
        )
    
    def validate(self, data: dict) -> List[str]:
        return []
    
    def transform(self, data: dict) -> dict:
        return {
            "applicationId": data.get("id"),
            "name": data.get("name"),
            "description": data.get("description"),
            "owner": data.get("owner"),
            "version": data.get("version")
        }


class ExtractorFacet(FacetPlugin):
    """Facet for Extractor metadata."""
    
    def __init__(self):
        super().__init__(
            name="extractor",
            schema_url="https://github.com/openlineage/OpenLineage/blob/main/spec/facets/ExtractorJobFacet.json"
        )
    
    def validate(self, data: dict) -> List[str]:
        return []
    
    def transform(self, data: dict) -> dict:
        return {
            "type": data.get("type"),
            "confidence": data.get("confidence"),
            "toolName": data.get("toolName"),
            "toolVersion": data.get("toolVersion")
        }


class ReviewFacet(FacetPlugin):
    """Facet for Code/Job Review metadata."""
    
    def __init__(self):
        super().__init__(
            name="review",
            schema_url="https://github.com/openlineage/OpenLineage/blob/main/spec/facets/ReviewJobFacet.json"
        )
    
    def validate(self, data: dict) -> List[str]:
        return []
    
    def transform(self, data: dict) -> dict:
        return {
            "lastReviewDate": data.get("lastReviewDate"),
            "lastReviewedByBrid": data.get("lastReviewedByBrid"),
            "reviewStatus": data.get("reviewStatus")
        }


class DataQualityFacet(FacetPlugin):
    """Custom facet for tracking data quality metrics."""
    
    def __init__(self):
        super().__init__(
            name="dataQuality",
            schema_url="https://github.com/openlineage/OpenLineage/blob/main/spec/facets/DataQualityDatasetFacet.json"
        )
    
    def validate(self, data: dict) -> List[str]:
        return []
    
    def transform(self, data: dict) -> dict:
        return {
            "completeness": data.get("completeness"),
            "accuracy": data.get("accuracy"),
            "lastChecked": data.get("lastChecked"),
            "reportUrl": data.get("reportUrl")
        }


def register(registry: FacetRegistry):
    """Register custom facets with the registry."""
    # Register dataset facets
    registry.register_dataset_facet("catalogue", CatalogueFacet())
    registry.register_dataset_facet("cde", CDEFacet())
    registry.register_dataset_facet("system", SystemFacet())
    registry.register_dataset_facet("dataQuality", DataQualityFacet())
    
    # Register job facets
    registry.register_job_facet("application", ApplicationFacet())
    registry.register_job_facet("extractor", ExtractorFacet())
    registry.register_job_facet("review", ReviewFacet())
