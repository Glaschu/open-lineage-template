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
import sys
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


def main() -> int:
    """Main entry point. Returns exit code."""
    parser = argparse.ArgumentParser(
        description="Convert YAML lineage definitions to OpenLineage events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
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
        "--skip-validation",
        action="store_true",
        help="Skip OpenLineage spec validation (not recommended)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        return run(args)
    except OpenLineageYAMLError as e:
        print(f"\n{e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run(args: argparse.Namespace) -> int:
    """Run the conversion pipeline."""
    print("=" * 60)
    print("OpenLineage YAML Tool")
    print("=" * 60)
    
    # Step 1: Load YAML files
    print(f"\n📁 Loading lineage definitions from: {args.root_folder}")
    loader = LineageLoader(args.root_folder)
    datasets, jobs = loader.load_all()
    
    print(f"   Found {len(datasets)} datasets and {len(jobs)} jobs")
    
    if not jobs:
        print("\n⚠️  No jobs found. Nothing to process.")
        return 0
    
    # Step 2: Validate YAML against schemas
    print("\n✅ Validating YAML schemas...")
    validator = SchemaValidator()
    
    errors = []
    for dataset_id, dataset in datasets.items():
        file_path = loader._dataset_files.get(dataset_id)
        dataset_errors = validator.validate_dataset(dataset, file_path)
        errors.extend(dataset_errors)
    
    for job_file, job_data in jobs:
        job_errors = validator.validate_job(job_data, job_file)
        errors.extend(job_errors)
    
    if errors:
        print(f"\n❌ Found {len(errors)} validation error(s):")
        for error in errors:
            print(f"\n{error}")
        return 1
    
    print("   All YAML files are valid")
    
    # Step 3: Convert to OpenLineage events
    print("\n🔄 Converting to OpenLineage events...")
    converter = OpenLineageConverter(loader, producer=args.producer)
    events = converter.convert_all()
    
    print(f"   Generated {len(events)} event(s)")
    
    # Step 4: Validate against OpenLineage spec
    if not args.skip_validation:
        print("\n🔍 Validating against OpenLineage spec...")
        ol_validator = OpenLineageValidator()
        
        for i, event in enumerate(events):
            spec_errors = ol_validator.validate(event)
            if spec_errors:
                job_name = event.get("job", {}).get("name", f"event {i+1}")
                print(f"\n❌ Event '{job_name}' failed spec validation:")
                for error in spec_errors:
                    print(f"   - {error}")
                return 1
        
        print("   All events conform to OpenLineage spec")
    
    # Step 5: Output or send events
    if args.output:
        print(f"\n💾 Writing events to: {args.output}")
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2)
        print(f"   Wrote {len(events)} events")
    
    if args.dry_run:
        print("\n📋 Dry run - events generated:")
        for event in events:
            job = event.get("job", {})
            inputs = len(event.get("inputs", []))
            outputs = len(event.get("outputs", []))
            print(f"   - {job.get('namespace')}/{job.get('name')}: {inputs} inputs, {outputs} outputs")
        
        if args.verbose:
            print("\n" + "-" * 60)
            print("Generated Events (JSON):")
            print("-" * 60)
            print(json.dumps(events, indent=2))
    
    elif args.api_url:
        print(f"\n📤 Sending events to: {args.api_url}")
        
        with OpenLineageSender(
            api_url=args.api_url,
            username=args.username,
            password=args.password
        ) as sender:
            sender.send_events(events)
        
        print(f"   ✅ Successfully sent {len(events)} event(s)")
    
    else:
        print("\n⚠️  No action specified. Use --dry-run, --output, or --api-url")
        return 0
    
    print("\n" + "=" * 60)
    print("✅ Complete!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
