import logging
import time

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.dolthub.com/api/v1alpha1"
HTTP_TIMEOUT = 30
POLL_INTERVAL = 1
POLL_TIMEOUT = 30


class DoltHubError(Exception):
    pass


class DoltHubClient:
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo

    def _headers(self) -> dict:
        return {"authorization": f"token {self.token}"}

    def execute_write(self, query: str) -> dict:
        """Execute a write query via DoltHub async API.

        1. POST the query to start the operation.
        2. Poll until the operation completes.
        """
        url = f"{BASE_URL}/{self.owner}/{self.repo}/write/main/main"
        resp = requests.post(
            url, headers=self._headers(), json={"query": query},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.json()

        if body.get("query_execution_status") != "Success":
            raise DoltHubError(
                f"Write failed: {body.get('query_execution_message')}"
            )

        operation_name = body["operation_name"]
        return self._poll_operation(operation_name)

    def _poll_operation(self, operation_name: str) -> dict:
        """Poll a write operation until it completes."""
        url = f"{BASE_URL}/{self.owner}/{self.repo}/write"
        deadline = time.monotonic() + POLL_TIMEOUT

        while time.monotonic() < deadline:
            try:
                resp = requests.get(
                    url,
                    headers=self._headers(),
                    params={"operationName": operation_name},
                    timeout=HTTP_TIMEOUT,
                )
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.warning(
                    "Poll request failed (write may have succeeded): %s", e
                )
                return {"done": True, "poll_failed": True}

            body = resp.json()

            if body.get("done"):
                status = body.get("res_details", {}).get(
                    "query_execution_status"
                )
                if status != "Success":
                    raise DoltHubError(
                        f"Operation failed: {body.get('res_details')}"
                    )
                logger.info("Write operation completed successfully")
                return body

            time.sleep(POLL_INTERVAL)

        logger.warning(
            "Poll timed out for %s (write may have succeeded)",
            operation_name,
        )
        return {"done": True, "poll_timed_out": True}
