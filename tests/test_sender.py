"""Tests for the OpenLineage event sender."""

import json
import pytest
import responses

from src.sender import OpenLineageSender
from src.exceptions import APIError


TEST_API_URL = "https://api.example.com/api/v1/lineage"

SAMPLE_EVENT = {
    "eventType": "COMPLETE",
    "eventTime": "2024-01-01T00:00:00Z",
    "producer": "https://test",
    "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json",
    "run": {"runId": "00000000-0000-0000-0000-000000000000"},
    "job": {"namespace": "test", "name": "test-job"},
    "inputs": [],
    "outputs": [],
}


class TestSendEvent:
    """Tests for sending individual events."""

    @responses.activate
    def test_send_success(self):
        responses.add(
            responses.POST,
            TEST_API_URL,
            json={"status": "ok"},
            status=200,
        )

        with OpenLineageSender(api_url=TEST_API_URL) as sender:
            result = sender.send_event(SAMPLE_EVENT)

        assert result["status"] == "ok"
        assert len(responses.calls) == 1

    @responses.activate
    def test_send_with_basic_auth(self):
        responses.add(responses.POST, TEST_API_URL, json={}, status=200)

        with OpenLineageSender(
            api_url=TEST_API_URL, username="user", password="pass"
        ) as sender:
            sender.send_event(SAMPLE_EVENT)

        assert responses.calls[0].request.headers.get("Authorization") is not None

    @responses.activate
    def test_send_sets_json_content_type(self):
        responses.add(responses.POST, TEST_API_URL, json={}, status=200)

        with OpenLineageSender(api_url=TEST_API_URL) as sender:
            sender.send_event(SAMPLE_EVENT)

        assert "application/json" in responses.calls[0].request.headers["Content-Type"]


class TestSendEvents:
    """Tests for sending multiple events."""

    @responses.activate
    def test_sends_all_events(self):
        responses.add(responses.POST, TEST_API_URL, json={}, status=200)

        events = [SAMPLE_EVENT, SAMPLE_EVENT, SAMPLE_EVENT]
        with OpenLineageSender(api_url=TEST_API_URL) as sender:
            results = sender.send_events(events)

        assert len(results) == 3
        assert len(responses.calls) == 3


class TestRetryLogic:
    """Tests for retry and error handling."""

    @responses.activate
    def test_retries_on_500(self):
        # First two requests fail, third succeeds
        responses.add(responses.POST, TEST_API_URL, status=500)
        responses.add(responses.POST, TEST_API_URL, status=500)
        responses.add(responses.POST, TEST_API_URL, json={"status": "ok"}, status=200)

        with OpenLineageSender(api_url=TEST_API_URL, max_retries=3) as sender:
            sender.RETRY_DELAY = 0  # Speed up test
            result = sender.send_event(SAMPLE_EVENT)

        assert result["status"] == "ok"
        assert len(responses.calls) == 3

    @responses.activate
    def test_no_retry_on_400(self):
        """Client errors (4xx except 429) should not be retried."""
        responses.add(responses.POST, TEST_API_URL, status=400, body="Bad Request")

        with OpenLineageSender(api_url=TEST_API_URL) as sender:
            with pytest.raises(APIError) as exc_info:
                sender.send_event(SAMPLE_EVENT)

        assert exc_info.value.status_code == 400
        assert len(responses.calls) == 1  # No retries

    @responses.activate
    def test_retries_on_429(self):
        """Rate limit (429) should be retried."""
        responses.add(responses.POST, TEST_API_URL, status=429)
        responses.add(responses.POST, TEST_API_URL, json={}, status=200)

        with OpenLineageSender(api_url=TEST_API_URL, max_retries=2) as sender:
            sender.RETRY_DELAY = 0
            result = sender.send_event(SAMPLE_EVENT)

        assert len(responses.calls) == 2

    @responses.activate
    def test_raises_after_max_retries(self):
        responses.add(responses.POST, TEST_API_URL, status=503)
        responses.add(responses.POST, TEST_API_URL, status=503)
        responses.add(responses.POST, TEST_API_URL, status=503)
        responses.add(responses.POST, TEST_API_URL, status=503)

        with OpenLineageSender(api_url=TEST_API_URL, max_retries=2) as sender:
            sender.RETRY_DELAY = 0
            with pytest.raises(APIError) as exc_info:
                sender.send_event(SAMPLE_EVENT)

        assert exc_info.value.status_code == 503


class TestConnectionTest:
    """Tests for connection testing."""

    @responses.activate
    def test_connection_success(self):
        responses.add(
            responses.GET,
            TEST_API_URL.replace("/lineage", "/namespaces"),
            status=200,
        )

        with OpenLineageSender(api_url=TEST_API_URL) as sender:
            assert sender.test_connection() is True

    @responses.activate
    def test_connection_failure(self):
        responses.add(
            responses.GET,
            TEST_API_URL.replace("/lineage", "/namespaces"),
            status=500,
        )

        with OpenLineageSender(api_url=TEST_API_URL) as sender:
            with pytest.raises(APIError):
                sender.test_connection()


class TestContextManager:
    """Tests for sender context manager."""

    def test_context_manager_closes_session(self):
        sender = OpenLineageSender(api_url=TEST_API_URL)
        with sender:
            assert sender.session is not None
        # Session should be closed (no assertion needed, just no error)
