#!/usr/bin/env python3
"""
OpenLineage YAML Tool - Main CLI Entry Point

Converts YAML lineage definitions to OpenLineage events and optionally sends to an API.

Usage:
    python -m src.main --root-folder ./lineage --dry-run
    python -m src.main --root-folder ./lineage --api-url https://api.example.com/api/v1/lineage
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from .loader import LineageLoader
from .validator import SchemaValidator, OpenLineageValidator
from .converter import OpenLineageConverter
from .sender import OpenLineageSender
from .exceptions import (
    OpenLineageYAMLError,
    YAMLParseError,
    YAMLValidationError,
    DatasetReferenceError,
    APIError
)

logger = logging.getLogger("openlineage-yaml-tool")

# Explicit exit codes
EXIT_SUCCESS = 0
EXIT_VALIDATION_ERROR = 1
EXIT_API_ERROR = 2
EXIT_CONFIG_ERROR = 3


def _configure_logging(log_level: str, log_format: str) -> None:
    """Configure the logging system."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    if log_format == "json":
        formatter = logging.Formatter(
            json.dumps({
                "timestamp": "%(asctime)s",
                "level": "%(levelname)s",
                "logger": "%(name)s",
                "message": "%(message)s",
            })
        )
    else:
        formatter = logging.Formatter("%(asctime)s [%(levelname)-7s] %(message)s", datefmt="%H:%M:%S")

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root = logging.getLogger("openlineage-yaml-tool")
    root.setLevel(level)
    root.addHandler(handler)

    # Also configure the src loggers
    for module in ("src.loader", "src.converter", "src.sender", "src.plugins"):
        mod_logger = logging.getLogger(module)
        mod_logger.setLevel(level)
        if not mod_logger.handlers:
            mod_logger.addHandler(handler)


def main() -> int:
    """Main entry point. Returns exit code."""
    parser = argparse.ArgumentParser(
        description="Convert YAML lineage definitions to OpenLineage events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate YAML only — no API connection needed
  python -m src.main --root-folder ./lineage --validate-only

  # Dry run - validate and show generated events
  python -m src.main --root-folder ./lineage --dry-run

  # Send to API with basic auth
  python -m src.main --root-folder ./lineage \\
      --api-url https://api.example.com/api/v1/lineage \\
      --username user --password pass

  # Output events to file
  python -m src.main --root-folder ./lineage --output events.json
        """
    )
    
    parser.add_argument(
        "--root-folder", "-r",
        type=Path,
        required=True,
        help="Path to the lineage folder containing datasets/ and jobs/"
    )
    
    parser.add_argument(
        "--api-url", "-u",
        type=str,
        help="OpenLineage API endpoint URL"
    )
    
    parser.add_argument(
        "--username",
        type=str,
        help="API username for basic auth"
    )
    
    parser.add_argument(
        "--password",
        type=str,
        help="API password for basic auth"
    )
    
    parser.add_argument(
        "--producer",
        type=str,
        help="Producer URL for OpenLineage events (default: auto-generated)"
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Validate and convert without sending to API"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file for generated events (JSON)"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate YAML files only (no conversion or API calls). "
             "Use this to check your YAML before running the pipeline."
    )
    
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip OpenLineage spec validation (not recommended)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Log output format (default: text)"
    )
    
    parser.add_argument(
        "--format",
        type=str,
        choices=["human", "json"],
        default="human",
        dest="output_format",
        help="CLI output format: 'human' for readable output, 'json' for machine-parseable summary"
    )
    
    args = parser.parse_args()
    
    # Verbose implies DEBUG
    if args.verbose and args.log_level == "INFO":
        args.log_level = "DEBUG"
    
    _configure_logging(args.log_level, args.log_format)
    
    try:
        return run(args)
    except YAMLValidationError as e:
        logger.error("%s", e)
        return EXIT_VALIDATION_ERROR
    except (YAMLParseError, DatasetReferenceError) as e:
        logger.error("%s", e)
        return EXIT_VALIDATION_ERROR
    except APIError as e:
        logger.error("%s", e)
        return EXIT_API_ERROR
    except OpenLineageYAMLError as e:
        logger.error("%s", e)
        return EXIT_CONFIG_ERROR
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return EXIT_CONFIG_ERROR


def run(args: argparse.Namespace) -> int:
    """Run the conversion pipeline."""
    start_time = time.monotonic()
    summary = {"status": "success", "applications": 0, "datasets": 0, "jobs": 0, "events": 0, "errors": []}

    logger.info("OpenLineage YAML Tool")
    
    # Step 1: Load YAML files
    logger.info("Loading lineage definitions from: %s", args.root_folder)
    loader = LineageLoader(args.root_folder)
    applications, datasets, jobs = loader.load_all()
    
    summary["applications"] = len(applications)
    summary["datasets"] = len(datasets)
    summary["jobs"] = len(jobs)
    logger.info("Found %d applications, %d datasets, and %d jobs", len(applications), len(datasets), len(jobs))
    
    if not jobs:
        logger.warning("No jobs found. Nothing to process.")
        summary["status"] = "no_jobs"
        _output_summary(args, summary, start_time)
        return EXIT_SUCCESS
    
    # Step 2: Validate YAML against schemas (per-section reporting)
    logger.info("Validating YAML schemas...")
    validator = SchemaValidator()
    total_errors = 0
    summary["validation"] = {"applications": [], "datasets": [], "jobs": []}
    
    # ── Applications ──
    app_errors = []
    for app_id, app_data in applications.items():
        errs = validator.validate_application(app_data, None)
        for e in errs:
            app_errors.append({"id": app_id, "error": e})
    
    if app_errors:
        logger.error("── Applications: %d error(s) ──", len(app_errors))
        for item in app_errors:
            logger.error("  [%s] %s", item["id"], item["error"])
        summary["validation"]["applications"] = [{"id": i["id"], "error": str(i["error"])} for i in app_errors]
        total_errors += len(app_errors)
    else:
        logger.info("  ✓ Applications: %d file(s) valid", len(applications))
    
    # ── Datasets ──
    ds_errors = []
    for dataset_id, dataset in datasets.items():
        file_path = loader._dataset_files.get(dataset_id)
        errs = validator.validate_dataset(dataset, file_path)
        for e in errs:
            ds_errors.append({"id": dataset_id, "file": str(file_path or "unknown"), "error": e})
    
    if ds_errors:
        logger.error("── Datasets: %d error(s) ──", len(ds_errors))
        for item in ds_errors:
            logger.error("  [%s] %s", item["id"], item["error"])
        summary["validation"]["datasets"] = [{"id": i["id"], "file": i["file"], "error": str(i["error"])} for i in ds_errors]
        total_errors += len(ds_errors)
    else:
        logger.info("  ✓ Datasets:     %d file(s) valid", len(datasets))
    
    # ── Jobs ──
    job_errors = []
    for job_file, job_data in jobs:
        job_id = job_data.get("id", str(job_file))
        errs = validator.validate_job(job_data, job_file)
        for e in errs:
            job_errors.append({"id": job_id, "file": str(job_file), "error": e})
    
    if job_errors:
        logger.error("── Jobs: %d error(s) ──", len(job_errors))
        for item in job_errors:
            logger.error("  [%s] %s", item["id"], item["error"])
        summary["validation"]["jobs"] = [{"id": i["id"], "file": i["file"], "error": str(i["error"])} for i in job_errors]
        total_errors += len(job_errors)
    else:
        logger.info("  ✓ Jobs:         %d file(s) valid", len(jobs))
    
    if total_errors > 0:
        logger.error("Validation failed: %d total error(s) across %d section(s)",
                     total_errors,
                     sum(1 for s in [app_errors, ds_errors, job_errors] if s))
        summary["status"] = "validation_failed"
        _output_summary(args, summary, start_time)
        return EXIT_VALIDATION_ERROR
    
    logger.info("All YAML files are valid")
    
    # If --validate-only, stop here
    if args.validate_only:
        logger.info("Validation passed — exiting (--validate-only mode)")
        summary["status"] = "validated"
        _output_summary(args, summary, start_time)
        return EXIT_SUCCESS
    
    # Step 3: Convert to OpenLineage events
    logger.info("Converting to OpenLineage events...")
    converter = OpenLineageConverter(loader, producer=args.producer)
    events = converter.convert_all()
    
    summary["events"] = len(events)
    logger.info("Generated %d event(s)", len(events))
    
    # Step 4: Validate against OpenLineage spec
    if not args.skip_validation:
        logger.info("Validating against OpenLineage spec...")
        ol_validator = OpenLineageValidator()
        
        for i, event in enumerate(events):
            spec_errors = ol_validator.validate(event)
            if spec_errors:
                job_name = event.get("job", {}).get("name", f"event {i+1}")
                logger.error("Event '%s' failed spec validation:", job_name)
                for error in spec_errors:
                    logger.error("  - %s", error)
                summary["status"] = "spec_validation_failed"
                summary["errors"] = spec_errors
                _output_summary(args, summary, start_time)
                return EXIT_VALIDATION_ERROR
        
        logger.info("All events conform to OpenLineage spec")
    
    # Step 5: Output or send events
    if args.output:
        logger.info("Writing events to: %s", args.output)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2)
        logger.info("Wrote %d events", len(events))
    
    if args.dry_run:
        logger.info("Dry run - events generated:")
        for event in events:
            job = event.get("job", {})
            inputs = len(event.get("inputs", []))
            outputs = len(event.get("outputs", []))
            logger.info("  - %s/%s: %d inputs, %d outputs", job.get('namespace'), job.get('name'), inputs, outputs)
        
        if args.verbose:
            logger.debug("Generated Events (JSON):\n%s", json.dumps(events, indent=2))
    
    elif args.api_url:
        logger.info("Sending events to: %s", args.api_url)
        
        with OpenLineageSender(
            api_url=args.api_url,
            username=args.username,
            password=args.password
        ) as sender:
            sender.send_events(events)
        
        logger.info("Successfully sent %d event(s)", len(events))
    
    else:
        logger.warning("No action specified. Use --dry-run, --output, or --api-url")
        _output_summary(args, summary, start_time)
        return EXIT_SUCCESS
    
    logger.info("Complete!")
    _output_summary(args, summary, start_time)
    return EXIT_SUCCESS


def _output_summary(args: argparse.Namespace, summary: dict, start_time: float) -> None:
    """Output a machine-readable summary if --format json is used."""
    summary["duration_seconds"] = round(time.monotonic() - start_time, 3)
    if getattr(args, 'output_format', 'human') == 'json':
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    sys.exit(main())
