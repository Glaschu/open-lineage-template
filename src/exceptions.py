"""
Custom exceptions for the OpenLineage YAML Tool.

All exceptions provide detailed, user-friendly error messages with context
about where the error occurred (file path, line number, JSON path).
"""

from typing import Optional, List, Any
from pathlib import Path


class OpenLineageYAMLError(Exception):
    """Base exception for all OpenLineage YAML tool errors."""
    
    def __init__(self, message: str, context: Optional[dict] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        return self.message


class YAMLParseError(OpenLineageYAMLError):
    """Error parsing a YAML file."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[Path] = None,
        line: Optional[int] = None,
        column: Optional[int] = None
    ):
        self.file_path = file_path
        self.line = line
        self.column = column
        super().__init__(message, {
            "file_path": str(file_path) if file_path else None,
            "line": line,
            "column": column
        })
    
    def format_message(self) -> str:
        parts = []
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        if self.line is not None:
            loc = f"Line {self.line}"
            if self.column is not None:
                loc += f", Column {self.column}"
            parts.append(loc)
        
        location = " @ ".join(parts) if parts else "Unknown location"
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ YAML PARSE ERROR                                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

Location: {location}

Error: {self.message}

Hint: Check for proper YAML syntax:
  - Correct indentation (use spaces, not tabs)
  - Proper quoting of strings with special characters
  - Valid YAML structure (lists use '- ', maps use 'key: value')
""".strip()


class YAMLValidationError(OpenLineageYAMLError):
    """Error validating YAML content against schema."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[Path] = None,
        schema_path: Optional[str] = None,
        expected: Optional[Any] = None,
        actual: Optional[Any] = None,
        suggestion: Optional[str] = None
    ):
        self.file_path = file_path
        self.schema_path = schema_path
        self.expected = expected
        self.actual = actual
        self.suggestion = suggestion
        super().__init__(message)
    
    def format_message(self) -> str:
        lines = [
            "╔══════════════════════════════════════════════════════════════════════════════╗",
            "║ YAML SCHEMA VALIDATION ERROR                                                 ║",
            "╚══════════════════════════════════════════════════════════════════════════════╝",
            ""
        ]
        
        if self.file_path:
            lines.append(f"File: {self.file_path}")
        if self.schema_path:
            lines.append(f"Path: {self.schema_path}")
        lines.append("")
        lines.append(f"Error: {self.message}")
        
        if self.expected is not None:
            lines.append(f"Expected: {self.expected}")
        if self.actual is not None:
            lines.append(f"Got: {self.actual}")
        if self.suggestion:
            lines.append("")
            lines.append(f"Suggestion: {self.suggestion}")
        
        return "\n".join(lines)


class DatasetReferenceError(OpenLineageYAMLError):
    """Error resolving a dataset reference from a job definition."""
    
    def __init__(
        self,
        referenced_id: str,
        job_file: Optional[Path] = None,
        available_datasets: Optional[List[str]] = None
    ):
        self.referenced_id = referenced_id
        self.job_file = job_file
        self.available_datasets = available_datasets or []
        super().__init__(f"Dataset '{referenced_id}' not found")
    
    def format_message(self) -> str:
        lines = [
            "╔══════════════════════════════════════════════════════════════════════════════╗",
            "║ DATASET REFERENCE ERROR                                                      ║",
            "╚══════════════════════════════════════════════════════════════════════════════╝",
            ""
        ]
        
        if self.job_file:
            lines.append(f"In job file: {self.job_file}")
        lines.append(f"Referenced dataset ID: '{self.referenced_id}'")
        lines.append("")
        lines.append("This dataset ID was not found in the datasets/ folder.")
        
        if self.available_datasets:
            lines.append("")
            lines.append("Available datasets:")
            for ds in sorted(self.available_datasets)[:10]:  # Show max 10
                lines.append(f"  - {ds}")
            if len(self.available_datasets) > 10:
                lines.append(f"  ... and {len(self.available_datasets) - 10} more")
            
            # Suggest similar names
            similar = self._find_similar(self.referenced_id, self.available_datasets)
            if similar:
                lines.append("")
                lines.append(f"Did you mean: {similar}?")
        
        return "\n".join(lines)
    
    def _find_similar(self, target: str, candidates: List[str]) -> Optional[str]:
        """Find the most similar dataset name (simple prefix/substring match)."""
        target_lower = target.lower()
        for candidate in candidates:
            if target_lower in candidate.lower() or candidate.lower() in target_lower:
                return candidate
        return None


class OpenLineageValidationError(OpenLineageYAMLError):
    """Error validating generated JSON against OpenLineage spec."""
    
    def __init__(
        self,
        message: str,
        json_path: Optional[str] = None,
        spec_reference: Optional[str] = None
    ):
        self.json_path = json_path
        self.spec_reference = spec_reference
        super().__init__(message)
    
    def format_message(self) -> str:
        lines = [
            "╔══════════════════════════════════════════════════════════════════════════════╗",
            "║ OPENLINEAGE SPEC VALIDATION ERROR                                            ║",
            "╚══════════════════════════════════════════════════════════════════════════════╝",
            "",
            "The generated OpenLineage event does not conform to the specification.",
            ""
        ]
        
        if self.json_path:
            lines.append(f"JSON Path: {self.json_path}")
        lines.append(f"Error: {self.message}")
        
        if self.spec_reference:
            lines.append("")
            lines.append(f"Spec Reference: {self.spec_reference}")
        
        lines.append("")
        lines.append("This is likely a bug in the tool. Please report this issue.")
        
        return "\n".join(lines)


class APIError(OpenLineageYAMLError):
    """Error communicating with the OpenLineage API."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        url: Optional[str] = None,
        retry_count: int = 0
    ):
        self.status_code = status_code
        self.response_body = response_body
        self.url = url
        self.retry_count = retry_count
        super().__init__(message)
    
    def format_message(self) -> str:
        lines = [
            "╔══════════════════════════════════════════════════════════════════════════════╗",
            "║ API ERROR                                                                    ║",
            "╚══════════════════════════════════════════════════════════════════════════════╝",
            ""
        ]
        
        if self.url:
            lines.append(f"URL: {self.url}")
        if self.status_code:
            lines.append(f"Status Code: {self.status_code}")
        if self.retry_count > 0:
            lines.append(f"Retries Attempted: {self.retry_count}")
        
        lines.append("")
        lines.append(f"Error: {self.message}")
        
        if self.response_body:
            lines.append("")
            lines.append("Response Body:")
            # Truncate long responses
            body = self.response_body[:500]
            if len(self.response_body) > 500:
                body += "... (truncated)"
            lines.append(body)
        
        # Add helpful suggestions based on status code
        if self.status_code:
            lines.append("")
            if self.status_code == 401:
                lines.append("Suggestion: Check your username and password credentials.")
            elif self.status_code == 403:
                lines.append("Suggestion: Your credentials may not have permission to post lineage events.")
            elif self.status_code == 404:
                lines.append("Suggestion: Verify the API URL is correct (typically ends with /api/v1/lineage).")
            elif self.status_code >= 500:
                lines.append("Suggestion: The API server is experiencing issues. Try again later.")
        
        return "\n".join(lines)
