"""
Example custom facet plugin.

To create your own facet plugin:
1. Create a Python file in the facets/ directory
2. Define a FacetPlugin subclass
3. Implement the register() function

This example shows how to create a data quality facet.
"""

from src.plugins import FacetPlugin, FacetRegistry
from typing import List


class DataQualityFacet(FacetPlugin):
    """Custom facet for tracking data quality metrics."""
    
    def __init__(self):
        super().__init__(
            name="dataQuality",
            schema_url="https://your-org.com/facets/data-quality-v1.json"
        )
    
    def validate(self, data: dict) -> List[str]:
        """Validate data quality facet data."""
        errors = []
        
        if 'score' in data:
            score = data['score']
            if not isinstance(score, (int, float)):
                errors.append("score must be a number")
            elif score < 0 or score > 100:
                errors.append("score must be between 0 and 100")
        
        if 'checks' in data and not isinstance(data['checks'], list):
            errors.append("checks must be a list")
        
        return errors
    
    def transform(self, data: dict) -> dict:
        """Transform data quality data."""
        result = {}
        
        if 'score' in data:
            result['qualityScore'] = float(data['score'])
        
        if 'checks' in data:
            result['qualityChecks'] = [
                {
                    "checkName": check.get('name', 'unnamed'),
                    "passed": check.get('passed', False),
                    "message": check.get('message')
                }
                for check in data['checks']
            ]
        
        if 'lastChecked' in data:
            result['lastCheckedAt'] = data['lastChecked']
        
        return result


class CostFacet(FacetPlugin):
    """Custom facet for tracking job execution costs."""
    
    def __init__(self):
        super().__init__(
            name="cost",
            schema_url="https://your-org.com/facets/cost-v1.json"
        )
    
    def validate(self, data: dict) -> List[str]:
        errors = []
        
        if 'computeUnits' in data:
            if not isinstance(data['computeUnits'], (int, float)):
                errors.append("computeUnits must be a number")
        
        if 'estimatedCost' in data:
            if not isinstance(data['estimatedCost'], (int, float)):
                errors.append("estimatedCost must be a number")
        
        return errors
    
    def transform(self, data: dict) -> dict:
        return {
            "computeUnits": data.get('computeUnits', 0),
            "estimatedCostUSD": data.get('estimatedCost', 0),
            "currency": data.get('currency', 'USD')
        }


def register(registry: FacetRegistry):
    """Register custom facets with the registry.
    
    This function is called automatically when the plugin is loaded.
    """
    # Register dataset facet
    registry.register_dataset_facet("dataQuality", DataQualityFacet())
    
    # Register job facet
    registry.register_job_facet("cost", CostFacet())
    
    # You can also register custom transformers
    def mask_pii(value: str) -> str:
        """Custom transformer to mask PII data."""
        if not value:
            return value
        if len(value) <= 4:
            return "****"
        return value[:2] + "*" * (len(value) - 4) + value[-2:]
    
    registry.register_transformer('MASK_PII', mask_pii)
