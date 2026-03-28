# P1 Meter Data Collector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python script that polls a P1 energy meter every 5 minutes and writes readings to DoltHub via their REST API.

**Architecture:** A single `collect.py` script fetches JSON from a local P1 meter, extracts energy fields, and POSTs an INSERT statement to the DoltHub async write API. A one-time `setup.py` creates the table. Managed with `uv`, deployed via cron on a Raspberry Pi.

**Tech Stack:** Python 3, `requests`, `uv`, DoltHub REST API

---

## File Structure

```
energy_inside/
├── pyproject.toml          # Project metadata and dependencies
├── src/
│   └── energy_inside/
│       ├── __init__.py
│       ├── dolthub.py      # DoltHub API client (write + poll)
│       ├── p1_meter.py     # P1 meter API client (fetch + extract + timestamp parsing)
│       └── sql.py          # SQL statement builder
├── collect.py              # Main entry point — fetch reading, write to DoltHub
├── setup.py                # One-time table creation
├── tests/
│   ├── test_dolthub.py
│   ├── test_p1_meter.py
│   └── test_sql.py
└── README.md
```

---

### Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `src/energy_inside/__init__.py`

- [ ] **Step 1: Initialize uv project**

```bash
cd /Users/thomas.dekeyser/checkouts_personal/energy_inside
uv init --lib --name energy-inside
```

This creates `pyproject.toml` and `src/energy_inside/__init__.py`.

- [ ] **Step 2: Add requests dependency**

```bash
uv add requests
```

- [ ] **Step 3: Add pytest as dev dependency**

```bash
uv add --dev pytest
```

- [ ] **Step 4: Verify setup**

```bash
uv run python -c "import energy_inside; print('ok')"
```

Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock src/energy_inside/__init__.py
git commit -m "chore: initialize uv project with requests and pytest"
```

---

### Task 2: P1 Meter Client — Timestamp Parsing

**Files:**
- Create: `src/energy_inside/p1_meter.py`
- Create: `tests/test_p1_meter.py`

- [ ] **Step 1: Write failing test for timestamp parsing**

Create `tests/test_p1_meter.py`:

```python
from energy_inside.p1_meter import parse_p1_timestamp


def test_parse_p1_timestamp():
    # 260326193000 = 2026-03-26 19:30:00
    result = parse_p1_timestamp(260326193000)
    assert result == "2026-03-26 19:30:00"


def test_parse_p1_timestamp_leading_zero():
    # 260101080500 = 2026-01-01 08:05:00
    result = parse_p1_timestamp(260101080500)
    assert result == "2026-01-01 08:05:00"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_p1_meter.py -v
```

Expected: FAIL with `ImportError` or `ModuleNotFoundError`

- [ ] **Step 3: Implement timestamp parsing**

Create `src/energy_inside/p1_meter.py`:

```python
from datetime import datetime


def parse_p1_timestamp(raw: int) -> str:
    """Parse P1 meter timestamp format YYMMDDHHmmss into 'YYYY-MM-DD HH:MM:SS'."""
    s = str(raw)
    dt = datetime.strptime(s, "%y%m%d%H%M%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_p1_meter.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/energy_inside/p1_meter.py tests/test_p1_meter.py
git commit -m "feat: add P1 meter timestamp parsing"
```

---

### Task 3: P1 Meter Client — Data Extraction

**Files:**
- Modify: `src/energy_inside/p1_meter.py`
- Modify: `tests/test_p1_meter.py`

- [ ] **Step 1: Write failing test for data extraction**

Append to `tests/test_p1_meter.py`:

```python
from energy_inside.p1_meter import extract_reading


def test_extract_reading():
    api_response = {
        "wifi_ssid": "Proximus-Home-2DB8",
        "wifi_strength": 78,
        "smr_version": 50,
        "meter_model": "LGF5E360",
        "unique_id": "314C475A30353638363430383338",
        "active_tariff": 2,
        "total_power_import_kwh": 1594.842,
        "total_power_import_t1_kwh": 739.591,
        "total_power_import_t2_kwh": 855.251,
        "total_power_export_kwh": 2355.869,
        "total_power_export_t1_kwh": 1729.965,
        "total_power_export_t2_kwh": 625.904,
        "active_power_w": 77.000,
        "active_power_l1_w": -2039.000,
        "active_power_l2_w": 89.000,
        "active_power_l3_w": 2027.000,
        "active_voltage_l1_v": 243.300,
        "active_voltage_l2_v": 241.700,
        "active_voltage_l3_v": 241.000,
        "active_current_a": 18.240,
        "active_current_l1_a": 8.400,
        "active_current_l2_a": 0.870,
        "active_current_l3_a": 8.970,
        "active_power_average_w": 45.000,
        "montly_power_peak_w": 3560.000,
        "montly_power_peak_timestamp": 260326193000,
        "total_gas_m3": 809.162,
        "gas_timestamp": 260328103406,
        "gas_unique_id": "2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D",
        "external": [],
    }

    reading = extract_reading(api_response)

    assert reading["active_tariff"] == 2
    assert reading["total_power_import_kwh"] == 1594.842
    assert reading["active_power_l1_w"] == -2039.000
    assert reading["monthly_power_peak_w"] == 3560.000
    assert reading["monthly_power_peak_timestamp"] == "2026-03-26 19:30:00"
    assert reading["total_gas_m3"] == 809.162
    assert reading["gas_timestamp"] == "2026-03-28 10:34:06"
    # Should not contain wifi/meter metadata
    assert "wifi_ssid" not in reading
    assert "meter_model" not in reading
    assert "external" not in reading
    # Should contain a timestamp key
    assert "timestamp" in reading
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_p1_meter.py::test_extract_reading -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement data extraction**

Add to `src/energy_inside/p1_meter.py`:

```python
from datetime import datetime, timezone

ENERGY_FIELDS = [
    "active_tariff",
    "total_power_import_kwh",
    "total_power_import_t1_kwh",
    "total_power_import_t2_kwh",
    "total_power_export_kwh",
    "total_power_export_t1_kwh",
    "total_power_export_t2_kwh",
    "active_power_w",
    "active_power_l1_w",
    "active_power_l2_w",
    "active_power_l3_w",
    "active_voltage_l1_v",
    "active_voltage_l2_v",
    "active_voltage_l3_v",
    "active_current_a",
    "active_current_l1_a",
    "active_current_l2_a",
    "active_current_l3_a",
    "active_power_average_w",
    "total_gas_m3",
]


def extract_reading(data: dict) -> dict:
    """Extract energy fields from P1 meter API response."""
    reading = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

    for field in ENERGY_FIELDS:
        reading[field] = data[field]

    # Fields with typo in API + rename
    reading["monthly_power_peak_w"] = data["montly_power_peak_w"]
    reading["monthly_power_peak_timestamp"] = parse_p1_timestamp(
        data["montly_power_peak_timestamp"]
    )
    reading["gas_timestamp"] = parse_p1_timestamp(data["gas_timestamp"])

    return reading
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_p1_meter.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/energy_inside/p1_meter.py tests/test_p1_meter.py
git commit -m "feat: add P1 meter data extraction"
```

---

### Task 4: SQL Statement Builder

**Files:**
- Create: `src/energy_inside/sql.py`
- Create: `tests/test_sql.py`

- [ ] **Step 1: Write failing test for INSERT builder**

Create `tests/test_sql.py`:

```python
from energy_inside.sql import build_insert, build_create_table


def test_build_insert():
    reading = {
        "timestamp": "2026-03-28 10:45:00",
        "active_tariff": 2,
        "total_power_import_kwh": 1594.842,
        "active_power_l1_w": -2039.0,
        "monthly_power_peak_timestamp": "2026-03-26 19:30:00",
    }

    sql = build_insert(reading)

    assert sql.startswith("REPLACE INTO readings")
    assert "'2026-03-28 10:45:00'" in sql
    assert "2" in sql
    assert "1594.842" in sql
    assert "-2039.0" in sql
    assert "'2026-03-26 19:30:00'" in sql


def test_build_insert_escapes_strings():
    reading = {
        "timestamp": "2026-03-28 10:45:00",
        "active_tariff": 1,
    }
    sql = build_insert(reading)
    assert "REPLACE INTO readings" in sql
    assert "'2026-03-28 10:45:00'" in sql
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_sql.py -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement SQL builder**

Create `src/energy_inside/sql.py`:

```python
COLUMNS = [
    "timestamp",
    "active_tariff",
    "total_power_import_kwh",
    "total_power_import_t1_kwh",
    "total_power_import_t2_kwh",
    "total_power_export_kwh",
    "total_power_export_t1_kwh",
    "total_power_export_t2_kwh",
    "active_power_w",
    "active_power_l1_w",
    "active_power_l2_w",
    "active_power_l3_w",
    "active_voltage_l1_v",
    "active_voltage_l2_v",
    "active_voltage_l3_v",
    "active_current_a",
    "active_current_l1_a",
    "active_current_l2_a",
    "active_current_l3_a",
    "active_power_average_w",
    "monthly_power_peak_w",
    "monthly_power_peak_timestamp",
    "total_gas_m3",
    "gas_timestamp",
]


def _format_value(value) -> str:
    """Format a value for SQL insertion."""
    if isinstance(value, str):
        return f"'{value}'"
    return str(value)


def build_insert(reading: dict) -> str:
    """Build a REPLACE INTO SQL statement from a reading dict."""
    cols = [c for c in COLUMNS if c in reading]
    vals = [_format_value(reading[c]) for c in cols]
    columns_str = ", ".join(cols)
    values_str = ", ".join(vals)
    return f"REPLACE INTO readings ({columns_str}) VALUES ({values_str})"


def build_create_table() -> str:
    """Build the CREATE TABLE IF NOT EXISTS statement for the readings table."""
    return """CREATE TABLE IF NOT EXISTS readings (
    timestamp DATETIME PRIMARY KEY,
    active_tariff INT,
    total_power_import_kwh DECIMAL(10,3),
    total_power_import_t1_kwh DECIMAL(10,3),
    total_power_import_t2_kwh DECIMAL(10,3),
    total_power_export_kwh DECIMAL(10,3),
    total_power_export_t1_kwh DECIMAL(10,3),
    total_power_export_t2_kwh DECIMAL(10,3),
    active_power_w DECIMAL(10,3),
    active_power_l1_w DECIMAL(10,3),
    active_power_l2_w DECIMAL(10,3),
    active_power_l3_w DECIMAL(10,3),
    active_voltage_l1_v DECIMAL(10,3),
    active_voltage_l2_v DECIMAL(10,3),
    active_voltage_l3_v DECIMAL(10,3),
    active_current_a DECIMAL(10,3),
    active_current_l1_a DECIMAL(10,3),
    active_current_l2_a DECIMAL(10,3),
    active_current_l3_a DECIMAL(10,3),
    active_power_average_w DECIMAL(10,3),
    monthly_power_peak_w DECIMAL(10,3),
    monthly_power_peak_timestamp DATETIME,
    total_gas_m3 DECIMAL(10,3),
    gas_timestamp DATETIME
)"""
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_sql.py -v
```

Expected: 2 passed

- [ ] **Step 5: Write test for CREATE TABLE**

Add to `tests/test_sql.py`:

```python
def test_build_create_table():
    sql = build_create_table()
    assert "CREATE TABLE IF NOT EXISTS readings" in sql
    assert "timestamp DATETIME PRIMARY KEY" in sql
    assert "total_power_import_kwh DECIMAL(10,3)" in sql
    assert "gas_timestamp DATETIME" in sql
```

- [ ] **Step 6: Run all tests**

```bash
uv run pytest tests/test_sql.py -v
```

Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add src/energy_inside/sql.py tests/test_sql.py
git commit -m "feat: add SQL statement builder for readings table"
```

---

### Task 5: DoltHub API Client

**Files:**
- Create: `src/energy_inside/dolthub.py`
- Create: `tests/test_dolthub.py`

- [ ] **Step 1: Write failing test for DoltHub client**

Create `tests/test_dolthub.py`:

```python
import json
from unittest.mock import patch, Mock
from energy_inside.dolthub import DoltHubClient


def _mock_post_response(operation_name="operations/test-uuid"):
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {
        "query_execution_status": "Success",
        "operation_name": operation_name,
    }
    resp.raise_for_status = Mock()
    return resp


def _mock_poll_response(done=True):
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {
        "_id": "operations/test-uuid",
        "done": done,
        "res_details": {
            "query_execution_status": "Success",
        },
    }
    resp.raise_for_status = Mock()
    return resp


@patch("energy_inside.dolthub.requests")
def test_execute_write(mock_requests):
    mock_requests.post.return_value = _mock_post_response()
    mock_requests.get.return_value = _mock_poll_response(done=True)

    client = DoltHubClient(
        token="test-token", owner="testowner", repo="testrepo"
    )
    result = client.execute_write("INSERT INTO t VALUES (1)")

    # Verify POST was called with correct URL and headers
    call_args = mock_requests.post.call_args
    assert "testowner/testrepo/write/main/main" in call_args[0][0]
    assert call_args[1]["headers"]["authorization"] == "token test-token"
    assert call_args[1]["json"]["query"] == "INSERT INTO t VALUES (1)"

    # Verify poll was called
    poll_args = mock_requests.get.call_args
    assert "operationName=operations/test-uuid" in poll_args[0][0] or \
           poll_args[1].get("params", {}).get("operationName") == "operations/test-uuid"

    assert result["res_details"]["query_execution_status"] == "Success"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_dolthub.py -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement DoltHub client**

Create `src/energy_inside/dolthub.py`:

```python
import logging
import time

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.dolthub.com/api/v1alpha1"
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
            url, headers=self._headers(), json={"query": query}
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
            resp = requests.get(
                url,
                headers=self._headers(),
                params={"operationName": operation_name},
            )
            resp.raise_for_status()
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

        raise DoltHubError(
            f"Operation {operation_name} timed out after {POLL_TIMEOUT}s"
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_dolthub.py -v
```

Expected: 1 passed

- [ ] **Step 5: Write test for poll retry**

Add to `tests/test_dolthub.py`:

```python
@patch("energy_inside.dolthub.time")
@patch("energy_inside.dolthub.requests")
def test_execute_write_polls_until_done(mock_requests, mock_time):
    mock_time.monotonic.side_effect = [0, 0, 1, 2]  # start, check, check, check
    mock_time.sleep = Mock()

    mock_requests.post.return_value = _mock_post_response()
    mock_requests.get.side_effect = [
        _mock_poll_response(done=False),
        _mock_poll_response(done=True),
    ]

    client = DoltHubClient(token="t", owner="o", repo="r")
    result = client.execute_write("INSERT INTO t VALUES (1)")

    assert mock_requests.get.call_count == 2
    assert result["done"] is True
```

- [ ] **Step 6: Run all tests**

```bash
uv run pytest tests/test_dolthub.py -v
```

Expected: 2 passed

- [ ] **Step 7: Commit**

```bash
git add src/energy_inside/dolthub.py tests/test_dolthub.py
git commit -m "feat: add DoltHub async write API client"
```

---

### Task 6: Main Collection Script

**Files:**
- Create: `collect.py`

- [ ] **Step 1: Create collect.py**

Create `collect.py`:

```python
"""Poll P1 meter and write reading to DoltHub."""

import logging
import os
import sys

import requests

from energy_inside.dolthub import DoltHubClient, DoltHubError
from energy_inside.p1_meter import extract_reading
from energy_inside.sql import build_insert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

P1_API_URL = os.environ.get("P1_API_URL", "http://192.168.1.12/api/v1/data")
DOLTHUB_TOKEN = os.environ.get("DOLTHUB_TOKEN", "")
DOLTHUB_OWNER = os.environ.get("DOLTHUB_OWNER", "thomasdekeyser")
DOLTHUB_REPO = os.environ.get("DOLTHUB_REPO", "energy_inside")


def main():
    if not DOLTHUB_TOKEN:
        logger.error("DOLTHUB_TOKEN environment variable is not set")
        sys.exit(1)

    # Fetch from P1 meter
    logger.info("Fetching data from P1 meter at %s", P1_API_URL)
    resp = requests.get(P1_API_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # Extract and build SQL
    reading = extract_reading(data)
    sql = build_insert(reading)
    logger.info("Inserting reading at %s", reading["timestamp"])

    # Write to DoltHub
    client = DoltHubClient(
        token=DOLTHUB_TOKEN, owner=DOLTHUB_OWNER, repo=DOLTHUB_REPO
    )
    client.execute_write(sql)
    logger.info("Done")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as e:
        logger.error("HTTP error: %s", e)
        sys.exit(1)
    except DoltHubError as e:
        logger.error("DoltHub error: %s", e)
        sys.exit(1)
```

- [ ] **Step 2: Verify it loads without errors**

```bash
DOLTHUB_TOKEN=fake uv run python -c "from collect import main; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add collect.py
git commit -m "feat: add main collection script"
```

---

### Task 7: Setup Script

**Files:**
- Create: `setup.py`

- [ ] **Step 1: Create setup.py**

Create `setup.py`:

```python
"""One-time setup: create the readings table on DoltHub."""

import logging
import os
import sys

from energy_inside.dolthub import DoltHubClient, DoltHubError
from energy_inside.sql import build_create_table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

DOLTHUB_TOKEN = os.environ.get("DOLTHUB_TOKEN", "")
DOLTHUB_OWNER = os.environ.get("DOLTHUB_OWNER", "thomasdekeyser")
DOLTHUB_REPO = os.environ.get("DOLTHUB_REPO", "energy_inside")


def main():
    if not DOLTHUB_TOKEN:
        logger.error("DOLTHUB_TOKEN environment variable is not set")
        sys.exit(1)

    client = DoltHubClient(
        token=DOLTHUB_TOKEN, owner=DOLTHUB_OWNER, repo=DOLTHUB_REPO
    )

    sql = build_create_table()
    logger.info("Creating readings table on %s/%s", DOLTHUB_OWNER, DOLTHUB_REPO)
    client.execute_write(sql)
    logger.info("Table created successfully")


if __name__ == "__main__":
    try:
        main()
    except DoltHubError as e:
        logger.error("DoltHub error: %s", e)
        sys.exit(1)
```

- [ ] **Step 2: Verify it loads without errors**

```bash
DOLTHUB_TOKEN=fake uv run python -c "from setup import main; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add setup.py
git commit -m "feat: add one-time table setup script"
```

---

### Task 8: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README**

Create `README.md`:

```markdown
# Energy Inside — P1 Meter Data Collector

Polls a HomeWizard P1 meter every 5 minutes and stores energy readings in DoltHub.

## Prerequisites

- Raspberry Pi on the same network as the P1 meter
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- DoltHub account with API token

## Setup

1. Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone and install:

```bash
git clone <repo-url> ~/energy_inside
cd ~/energy_inside
uv sync
```

3. Set your DoltHub token:

```bash
export DOLTHUB_TOKEN=your_token_here
```

4. Create the database table (one-time):

```bash
uv run python setup.py
```

5. Test a single collection:

```bash
uv run python collect.py
```

6. Add cron job for 5-minute polling:

```bash
crontab -e
```

Add this line:

```
*/5 * * * * DOLTHUB_TOKEN=your_token_here cd /home/pi/energy_inside && /home/pi/.local/bin/uv run python collect.py >> /home/pi/energy_inside/collect.log 2>&1
```

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|---|---|---|
| `DOLTHUB_TOKEN` | (required) | DoltHub API token |
| `P1_API_URL` | `http://192.168.1.12/api/v1/data` | P1 meter API endpoint |
| `DOLTHUB_OWNER` | `thomasdekeyser` | DoltHub repository owner |
| `DOLTHUB_REPO` | `energy_inside` | DoltHub repository name |

## Logs

Logs are appended to `collect.log`. Check for errors:

```bash
tail -f ~/energy_inside/collect.log
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup instructions"
```

---

### Task 9: Run All Tests

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: All tests pass (7 total)

- [ ] **Step 2: Final commit if any cleanup needed**

```bash
git status
```
