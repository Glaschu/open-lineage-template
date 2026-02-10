"""
Validator module for validating YAML content against JSON schemas.

Provides detailed error messages with paths to help users fix issues.
"""

import json
from pathlib import Path
from typing import Optional, List, Tuple, Any

from jsonschema import Draft202012Validator, ValidationError
from jsonschema.exceptions import best_match

from .exceptions import YAMLValidationError


class SchemaValidator:
    """Validates YAML content against JSON schemas."""
    
    # Default schema paths relative to project root
    SCHEMA_DIR = Path(__file__).parent.parent / "schemas"
    
    def __init__(self, schema_dir: Optional[Path] = None):
        """
        Initialize the validator with schema directory.
        
        Args:
            schema_dir: Optional path to schemas directory
        """
        self.schema_dir = Path(schema_dir) if schema_dir else self.SCHEMA_DIR
        
        # Load schemas
        self._dataset_schema = self._load_schema("dataset.schema.json")
        self._job_schema = self._load_schema("job.schema.json")
        
        # Create validators
        self._dataset_validator = Draft202012Validator(self._dataset_schema)
        self._job_validator = Draft202012Validator(self._job_schema)
    
    def _load_schema(self, filename: str) -> dict:
        """Load a JSON schema file."""
        schema_path = self.schema_dir / filename
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_dataset(
        self,
        data: dict,
        file_path: Optional[Path] = None
    ) -> List[YAMLValidationError]:
        """
        Validate a dataset definition against the schema.
        
        Args:
            data: Dataset definition dictionary
            file_path: Optional source file path for error messages
            
        Returns:
            List of validation errors (empty if valid)
        """
        return self._validate(data, self._dataset_validator, file_path, "dataset")
    
    def validate_job(
        self,
        data: dict,
        file_path: Optional[Path] = None
    ) -> List[YAMLValidationError]:
        """
        Validate a job definition against the schema.
        
        Args:
            data: Job definition dictionary
            file_path: Optional source file path for error messages
            
        Returns:
            List of validation errors (empty if valid)
        """
        return self._validate(data, self._job_validator, file_path, "job")
    
    def _validate(
        self,
        data: dict,
        validator: Draft202012Validator,
        file_path: Optional[Path],
        kind: str
    ) -> List[YAMLValidationError]:
        """
        Run validation and collect errors.
        
        Returns list of formatted validation errors.
        """
        errors = list(validator.iter_errors(data))
        
        if not errors:
            return []
        
        result = []
        for error in errors:
            # Build a readable path
            path = self._format_path(error.absolute_path)
            
            # Get suggestion based on error type
            suggestion = self._get_suggestion(error, kind)
            
            result.append(YAMLValidationError(
                message=error.message,
                file_path=file_path,
                schema_path=path,
                expected=self._format_expected(error),
                actual=self._format_actual(error),
                suggestion=suggestion
            ))
        
        return result
    
    def _format_path(self, path) -> str:
        """Format JSON path for display."""
        if not path:
            return "(root)"
        
        parts = []
        for p in path:
            if isinstance(p, int):
                parts.append(f"[{p}]")
            else:
                if parts:
                    parts.append(f".{p}")
                else:
                    parts.append(str(p))
        
        return "".join(parts)
    
    def _format_expected(self, error: ValidationError) -> Optional[str]:
        """Extract expected value from validation error."""
        if error.validator == "type":
            return f"type '{error.validator_value}'"
        elif error.validator == "enum":
            return f"one of {error.validator_value}"
        elif error.validator == "required":
            return f"required field(s): {error.validator_value}"
        elif error.validator == "const":
            return f"value '{error.validator_value}'"
        elif error.validator == "pattern":
            return f"pattern matching '{error.validator_value}'"
        return None
    
    def _format_actual(self, error: ValidationError) -> Optional[str]:
        """Extract actual value from validation error."""
        if error.validator == "type":
            return f"type '{type(error.instance).__name__}'"
        elif error.instance is not None and not isinstance(error.instance, (dict, list)):
            return f"'{error.instance}'"
        return None
    
    def _get_suggestion(self, error: ValidationError, kind: str) -> Optional[str]:
        """Generate helpful suggestion based on error."""
        if error.validator == "required":
            missing = error.validator_value
            if isinstance(missing, list) and len(missing) == 1:
                field = missing[0]
                if field == "id":
                    return f"Add 'id: your_{kind}_id' to uniquely identify this {kind}"
                elif field == "namespace":
                    return "Add 'namespace: postgres://host:port' or similar"
                elif field == "name":
                    return "Add 'name: your.dataset.name' (e.g., schema.table)"
        
        elif error.validator == "const":
            if "kind" in str(error.absolute_path):
                return f"This file should have 'kind: {kind}'"
            elif "version" in str(error.absolute_path):
                return "Use 'version: 1'"
        
        elif error.validator == "additionalProperties":
            return "Remove or rename the unknown field"
        
        return None


class OpenLineageValidator:
    """Validates generated OpenLineage events against the spec."""
    
    SPEC_PATH = Path(__file__).parent.parent / "schemas" / "openlineage-spec.json"
    
    def __init__(self, spec_path: Optional[Path] = None):
        """
        Initialize with OpenLineage spec.
        
        Args:
            spec_path: Optional path to OpenLineage spec JSON
        """
        self.spec_path = Path(spec_path) if spec_path else self.SPEC_PATH
        self._spec = self._load_spec()
        self._validator = Draft202012Validator(self._spec)
    
    def _load_spec(self) -> dict:
        """Load the OpenLineage spec."""
        if not self.spec_path.exists():
            raise FileNotFoundError(
                f"OpenLineage spec not found: {self.spec_path}\n"
                "Run: curl -o schemas/openlineage-spec.json "
                "https://raw.githubusercontent.com/OpenLineage/OpenLineage/main/spec/OpenLineage.json"
            )
        
        with open(self.spec_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate(self, event: dict) -> List[str]:
        """
        Validate an OpenLineage event against the spec.
        
        Args:
            event: OpenLineage event dictionary
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = list(self._validator.iter_errors(event))
        
        if not errors:
            return []
        
        # Return the most relevant error first
        main_error = best_match(errors)
        result = [self._format_error(main_error)]
        
        # Add other significant errors
        for error in errors:
            if error is not main_error:
                formatted = self._format_error(error)
                if formatted not in result:
                    result.append(formatted)
        
        return result[:5]  # Limit to 5 errors
    
    def _format_error(self, error: ValidationError) -> str:
        """Format a validation error for display."""
        path = "/".join(str(p) for p in error.absolute_path) or "(root)"
        return f"At '{path}': {error.message}"
