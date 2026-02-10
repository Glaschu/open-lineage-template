"""
Sender module for posting OpenLineage events to an API.

Supports authentication, retries, and detailed error reporting.
"""

import json
import logging
import time
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

import requests
from requests.auth import HTTPBasicAuth

from .exceptions import APIError


class OpenLineageSender:
    """Sends OpenLineage events to an API endpoint."""
    
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds (doubles each retry)
    
    def __init__(
        self,
        api_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize the sender.
        
        Args:
            api_url: Base URL for the OpenLineage API (e.g., https://api.example.com/api/v1/lineage)
            username: Optional username for basic auth
            password: Optional password for basic auth
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_url = api_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Set up authentication
        self.auth = None
        if username and password:
            self.auth = HTTPBasicAuth(username, password)
        
        # Set up session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
    
    def send_event(self, event: dict) -> dict:
        """
        Send a single OpenLineage event.
        
        Args:
            event: OpenLineage event dictionary
            
        Returns:
            Response data from the API
            
        Raises:
            APIError: If the request fails after retries
        """
        return self._send_with_retry(event)
    
    def send_events(self, events: List[dict]) -> List[dict]:
        """
        Send multiple OpenLineage events.
        
        Args:
            events: List of OpenLineage event dictionaries
            
        Returns:
            List of response data from the API
            
        Raises:
            APIError: If any request fails after retries
        """
        results = []
        for i, event in enumerate(events, 1):
            logger.info("Sending event %d/%d...", i, len(events))
            result = self.send_event(event)
            results.append(result)
        
        return results
    
    def _send_with_retry(self, event: dict) -> dict:
        """Send with exponential backoff retry."""
        last_error = None
        delay = self.RETRY_DELAY
        
        for attempt in range(self.max_retries + 1):
            try:
                return self._send_request(event)
            
            except APIError as e:
                last_error = e
                
                # Don't retry client errors (4xx) except 429 (rate limit)
                if e.status_code and 400 <= e.status_code < 500 and e.status_code != 429:
                    raise
                
                if attempt < self.max_retries:
                    logger.info("Retry %d/%d in %ds...", attempt + 1, self.max_retries, delay)
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
        
        # All retries exhausted
        if last_error:
            last_error.retry_count = self.max_retries
            raise last_error
        
        raise APIError("Unknown error after retries")
    
    def _send_request(self, event: dict) -> dict:
        """Send a single HTTP request."""
        try:
            response = self.session.post(
                self.api_url,
                data=json.dumps(event),
                auth=self.auth,
                timeout=self.timeout
            )
            
            # Check for HTTP errors
            if not response.ok:
                raise APIError(
                    message=f"HTTP {response.status_code}: {response.reason}",
                    status_code=response.status_code,
                    response_body=response.text,
                    url=self.api_url
                )
            
            # Try to parse response as JSON
            try:
                return response.json() if response.text else {}
            except json.JSONDecodeError:
                return {"status": "ok", "raw_response": response.text}
        
        except requests.exceptions.Timeout:
            raise APIError(
                message=f"Request timed out after {self.timeout} seconds",
                url=self.api_url
            )
        
        except requests.exceptions.ConnectionError as e:
            raise APIError(
                message=f"Connection failed: {str(e)}",
                url=self.api_url
            )
        
        except requests.exceptions.RequestException as e:
            raise APIError(
                message=f"Request failed: {str(e)}",
                url=self.api_url
            )
    
    def test_connection(self) -> bool:
        """
        Test the API connection with a simple request.
        
        Returns:
            True if connection is successful
            
        Raises:
            APIError: If connection fails
        """
        try:
            # Try a simple GET to check if the API is reachable
            response = self.session.get(
                self.api_url.replace("/lineage", "/namespaces") if "/lineage" in self.api_url else self.api_url,
                auth=self.auth,
                timeout=10
            )
            
            # Accept any successful response
            if response.ok or response.status_code == 404:
                return True
            
            raise APIError(
                message=f"API returned {response.status_code}",
                status_code=response.status_code,
                url=self.api_url
            )
        
        except requests.exceptions.RequestException as e:
            raise APIError(
                message=f"Connection test failed: {str(e)}",
                url=self.api_url
            )
    
    def close(self) -> None:
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
