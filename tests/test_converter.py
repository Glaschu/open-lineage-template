"""Tests for the OpenLineage event converter."""

import pytest
from datetime import datetime, timezone

from src.loader import LineageLoader
from src.converter import OpenLineageConverter, OPENLINEAGE_SCHEMA_URL


class TestConvertAll:
    """Tests for full pipeline conversion."""

    def test_converts_all_jobs_to_events(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader)
        events = converter.convert_all()

        assert len(events) == 1

    def test_event_has_required_fields(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader)
        events = converter.convert_all()
        event = events[0]

        assert event["eventType"] == "COMPLETE"
        assert "eventTime" in event
        assert "producer" in event
        assert event["schemaURL"] == OPENLINEAGE_SCHEMA_URL
        assert "run" in event
        assert "job" in event
        assert "inputs" in event
        assert "outputs" in event

    def test_run_has_uuid(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader)
        events = converter.convert_all()

        run_id = events[0]["run"]["runId"]
        # Basic UUID format check
        assert len(run_id) == 36
        assert run_id.count("-") == 4

    def test_custom_producer_url(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader, producer="https://my-org/tool/v2")
        events = converter.convert_all()

        assert events[0]["producer"] == "https://my-org/tool/v2"

    def test_custom_event_time(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        fixed_time = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        converter = OpenLineageConverter(loader, event_time=fixed_time)
        events = converter.convert_all()

        assert events[0]["eventTime"] == "2024-06-15T12:00:00+00:00"


class TestJobConversion:
    """Tests for job section of event."""

    def test_job_namespace_and_name(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader)
        events = converter.convert_all()
        job = events[0]["job"]

        assert job["namespace"] == "airflow"
        assert job["name"] == "test-etl-job"

    def test_job_description_becomes_documentation_facet(self, populated_lineage):
        import yaml
        job_file = populated_lineage / "jobs" / "test_etl.yaml"
        job_data = yaml.safe_load(job_file.read_text())
        job_data["description"] = "A test ETL process"
        job_file.write_text(yaml.dump(job_data))

        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader)
        events = converter.convert_all()

        facets = events[0]["job"].get("facets", {})
        assert "documentation" in facets
        assert facets["documentation"]["description"] == "A test ETL process"


class TestInputOutputConversion:
    """Tests for inputs/outputs resolution."""

    def test_inputs_resolved_from_refs(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader)
        events = converter.convert_all()

        inputs = events[0]["inputs"]
        assert len(inputs) == 1
        assert inputs[0]["name"] == "public.test_table"
        assert inputs[0]["namespace"] == "postgres://localhost:5432"

    def test_outputs_resolved_from_refs(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader)
        events = converter.convert_all()

        outputs = events[0]["outputs"]
        assert len(outputs) == 1
        assert outputs[0]["name"] == "public.test_output"

    def test_schema_facet_on_input(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader)
        events = converter.convert_all()

        input_ds = events[0]["inputs"][0]
        schema = input_ds.get("facets", {}).get("schema", {})
        fields = schema.get("fields", [])
        field_names = [f["name"] for f in fields]

        assert "id" in field_names
        assert "email" in field_names

    def test_ownership_facet_on_input(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader)
        events = converter.convert_all()

        input_ds = events[0]["inputs"][0]
        ownership = input_ds.get("facets", {}).get("ownership", {})
        owners = ownership.get("owners", [])
        assert len(owners) == 1
        assert owners[0]["name"] == "data-team"


class TestColumnLineage:
    """Tests for column-level lineage conversion."""

    def test_column_lineage_on_output(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader)
        events = converter.convert_all()

        output = events[0]["outputs"][0]
        col_lineage = output.get("facets", {}).get("columnLineage", {})
        fields = col_lineage.get("fields", {})

        assert "out_id" in fields
        input_fields = fields["out_id"]["inputFields"]
        assert len(input_fields) == 1
        assert input_fields[0]["field"] == "id"
        assert input_fields[0]["name"] == "public.test_table"

    def test_transformation_type_mapping(self, populated_lineage):
        loader = LineageLoader(populated_lineage)
        loader.load_all()
        converter = OpenLineageConverter(loader)
        events = converter.convert_all()

        output = events[0]["outputs"][0]
        fields = output["facets"]["columnLineage"]["fields"]
        transform = fields["out_id"]["inputFields"][0]["transformations"][0]

        assert transform["type"] == "DIRECT"
        assert transform["subtype"] == "IDENTITY"
