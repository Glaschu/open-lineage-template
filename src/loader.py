"""
Loader module for loading and resolving YAML lineage definitions.

This module handles:
- Loading all dataset YAML files from the datasets/ folder
- Loading all job YAML files from the jobs/ folder
- Resolving dataset references in jobs to actual dataset definitions
"""

import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from .exceptions import YAMLParseError, DatasetReferenceError


class LineageLoader:
    """Loads and resolves lineage YAML definitions."""
    
    def __init__(self, root_folder: Path):
        """
        Initialize the loader with a root lineage folder.
        
        Args:
            root_folder: Path to the lineage folder containing datasets/ and jobs/
        """
        self.root_folder = Path(root_folder)
        self.datasets_folder = self.root_folder / "datasets"
        self.jobs_folder = self.root_folder / "jobs"
        
        # Cache for loaded datasets (id -> definition)
        self._datasets: Dict[str, dict] = {}
        self._dataset_files: Dict[str, Path] = {}  # id -> file path
        
        # Cache for loaded jobs
        self._jobs: List[Tuple[Path, dict]] = []
    
    def load_all(self) -> Tuple[Dict[str, dict], List[Tuple[Path, dict]]]:
        """
        Load all datasets and jobs from the lineage folder.
        
        Returns:
            Tuple of (datasets dict, list of (file_path, job_data) tuples)
            
        Raises:
            YAMLParseError: If any YAML file cannot be parsed
            FileNotFoundError: If required folders don't exist
        """
        self._validate_folder_structure()
        self._load_datasets()
        self._load_jobs()
        
        return self._datasets, self._jobs
    
    def _validate_folder_structure(self) -> None:
        """Validate that the required folder structure exists."""
        if not self.root_folder.exists():
            raise FileNotFoundError(
                f"Lineage folder not found: {self.root_folder}\n"
                f"Expected folder structure:\n"
                f"  {self.root_folder}/\n"
                f"    ├── datasets/\n"
                f"    │   └── *.yaml\n"
                f"    └── jobs/\n"
                f"        └── *.yaml"
            )
        
        if not self.datasets_folder.exists():
            raise FileNotFoundError(
                f"Datasets folder not found: {self.datasets_folder}\n"
                f"Create this folder and add dataset YAML files."
            )
        
        if not self.jobs_folder.exists():
            raise FileNotFoundError(
                f"Jobs folder not found: {self.jobs_folder}\n"
                f"Create this folder and add job YAML files."
            )
    
    def _load_datasets(self) -> None:
        """Load all dataset YAML files recursively."""
        yaml_files = list(self.datasets_folder.rglob("*.yaml")) + \
                     list(self.datasets_folder.rglob("*.yml"))
        
        if not yaml_files:
            print(f"Warning: No dataset files found in {self.datasets_folder}")
            return
        
        for file_path in yaml_files:
            data = self._load_yaml_file(file_path)
            
            # Validate it's a dataset
            if data.get("kind") != "dataset":
                raise YAMLParseError(
                    f"Expected 'kind: dataset', got '{data.get('kind', 'missing')}'",
                    file_path=file_path
                )
            
            dataset_id = data.get("id")
            if not dataset_id:
                raise YAMLParseError(
                    "Dataset is missing required 'id' field",
                    file_path=file_path
                )
            
            # Check for duplicate IDs
            if dataset_id in self._datasets:
                raise YAMLParseError(
                    f"Duplicate dataset ID '{dataset_id}' found.\n"
                    f"First defined in: {self._dataset_files[dataset_id]}\n"
                    f"Also defined in: {file_path}",
                    file_path=file_path
                )
            
            self._datasets[dataset_id] = data
            self._dataset_files[dataset_id] = file_path
            print(f"  Loaded dataset: {dataset_id} ({file_path.relative_to(self.root_folder)})")
    
    def _load_jobs(self) -> None:
        """Load all job YAML files recursively."""
        yaml_files = list(self.jobs_folder.rglob("*.yaml")) + \
                     list(self.jobs_folder.rglob("*.yml"))
        
        if not yaml_files:
            print(f"Warning: No job files found in {self.jobs_folder}")
            return
        
        for file_path in yaml_files:
            data = self._load_yaml_file(file_path)
            
            # Validate it's a job
            if data.get("kind") != "job":
                raise YAMLParseError(
                    f"Expected 'kind: job', got '{data.get('kind', 'missing')}'",
                    file_path=file_path
                )
            
            self._jobs.append((file_path, data))
            print(f"  Loaded job: {data.get('id', 'unknown')} ({file_path.relative_to(self.root_folder)})")
    
    def _load_yaml_file(self, file_path: Path) -> dict:
        """
        Load and parse a YAML file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Parsed YAML content as a dictionary
            
        Raises:
            YAMLParseError: If the file cannot be parsed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                
            if content is None:
                raise YAMLParseError(
                    "File is empty or contains only comments",
                    file_path=file_path
                )
            
            if not isinstance(content, dict):
                raise YAMLParseError(
                    f"Expected a YAML mapping (dictionary), got {type(content).__name__}",
                    file_path=file_path
                )
            
            return content
            
        except yaml.YAMLError as e:
            # Extract line/column info from YAML error if available
            line = None
            column = None
            if hasattr(e, 'problem_mark') and e.problem_mark:
                line = e.problem_mark.line + 1
                column = e.problem_mark.column + 1
            
            raise YAMLParseError(
                str(e),
                file_path=file_path,
                line=line,
                column=column
            )
    
    def resolve_dataset_reference(
        self,
        ref_id: str,
        job_file: Optional[Path] = None
    ) -> dict:
        """
        Resolve a dataset reference to its full definition.
        
        Args:
            ref_id: Dataset ID to resolve
            job_file: Path to the job file making the reference (for error messages)
            
        Returns:
            The full dataset definition dictionary
            
        Raises:
            DatasetReferenceError: If the dataset ID is not found
        """
        if ref_id not in self._datasets:
            raise DatasetReferenceError(
                referenced_id=ref_id,
                job_file=job_file,
                available_datasets=list(self._datasets.keys())
            )
        
        return self._datasets[ref_id]
    
    def get_dataset_ids(self) -> List[str]:
        """Get list of all loaded dataset IDs."""
        return list(self._datasets.keys())
    
    def get_job_count(self) -> int:
        """Get number of loaded jobs."""
        return len(self._jobs)
