# P1 Meter Data Collector — Design Spec

## Overview

A Python script that polls a local P1 meter API every 5 minutes (via cron on a Raspberry Pi) and writes energy data directly to DoltHub via their REST API.

## Architecture

```
[P1 Meter @ 192.168.1.12] --HTTP--> [Python script on RPi] --HTTPS--> [DoltHub API: thomasdekeyser/energy_inside]
```

- The P1 meter exposes a local HTTP API at `http://192.168.1.12/api/v1/data`
- The Python script runs on a Raspberry Pi on the same local network
- Data is written to DoltHub using their async write REST API — no local Dolt installation required

## Data Schema

Single `readings` table on the `main` branch of `thomasdekeyser/energy_inside`.

| Column                        | Type            | Source field                   |
| ----------------------------- | --------------- | ------------------------------ |
| `timestamp`                   | `DATETIME` (PK) | poll time (UTC)               |
| `active_tariff`               | `INT`           | `active_tariff`                |
| `total_power_import_kwh`      | `DECIMAL(10,3)` | `total_power_import_kwh`       |
| `total_power_import_t1_kwh`   | `DECIMAL(10,3)` | `total_power_import_t1_kwh`    |
| `total_power_import_t2_kwh`   | `DECIMAL(10,3)` | `total_power_import_t2_kwh`    |
| `total_power_export_kwh`      | `DECIMAL(10,3)` | `total_power_export_kwh`       |
| `total_power_export_t1_kwh`   | `DECIMAL(10,3)` | `total_power_export_t1_kwh`    |
| `total_power_export_t2_kwh`   | `DECIMAL(10,3)` | `total_power_export_t2_kwh`    |
| `active_power_w`              | `DECIMAL(10,3)` | `active_power_w`               |
| `active_power_l1_w`           | `DECIMAL(10,3)` | `active_power_l1_w`            |
| `active_power_l2_w`           | `DECIMAL(10,3)` | `active_power_l2_w`            |
| `active_power_l3_w`           | `DECIMAL(10,3)` | `active_power_l3_w`            |
| `active_voltage_l1_v`         | `DECIMAL(10,3)` | `active_voltage_l1_v`          |
| `active_voltage_l2_v`         | `DECIMAL(10,3)` | `active_voltage_l2_v`          |
| `active_voltage_l3_v`         | `DECIMAL(10,3)` | `active_voltage_l3_v`          |
| `active_current_a`            | `DECIMAL(10,3)` | `active_current_a`             |
| `active_current_l1_a`         | `DECIMAL(10,3)` | `active_current_l1_a`          |
| `active_current_l2_a`         | `DECIMAL(10,3)` | `active_current_l2_a`          |
| `active_current_l3_a`         | `DECIMAL(10,3)` | `active_current_l3_a`          |
| `active_power_average_w`      | `DECIMAL(10,3)` | `active_power_average_w`       |
| `monthly_power_peak_w`        | `DECIMAL(10,3)` | `montly_power_peak_w`          |
| `monthly_power_peak_timestamp`| `DATETIME`      | `montly_power_peak_timestamp`  |
| `total_gas_m3`                | `DECIMAL(10,3)` | `total_gas_m3`                 |
| `gas_timestamp`               | `DATETIME`      | `gas_timestamp`                |

Notes:
- The source API has a typo (`montly_power_peak_w`). The column name is corrected to `monthly_power_peak_w`.
- `montly_power_peak_timestamp` and `gas_timestamp` are returned as `YYMMDDHHmmss` integers (e.g., `260326193000` = 2026-03-26 19:30:00). The script parses these into `DATETIME` values before inserting.

## DoltHub Write API Flow

The DoltHub write API is asynchronous:

1. **POST** `https://www.dolthub.com/api/v1alpha1/thomasdekeyser/energy_inside/write/main/main`
   - Header: `Authorization: token <DOLTHUB_TOKEN>`
   - Body: `{"query": "INSERT INTO readings (...) VALUES (...)"}`
   - Returns: an operation ID
2. **GET** the operation status endpoint until completion

## Script Behavior (`collect.py`)

1. Fetch JSON from `http://192.168.1.12/api/v1/data`
2. Extract the energy-related fields (skip wifi, meter metadata, external array)
3. Record the current UTC timestamp
4. Build an `INSERT INTO readings` SQL statement with the extracted values
5. POST the SQL to DoltHub's write API
6. Poll the operation endpoint until complete
7. Log success or failure to stdout (captured by cron/syslog)

## Table Setup

The `readings` table must be created manually via the DoltHub web SQL console before first use, as the DoltHub write API requires an existing commit history.

## Configuration

- `DOLTHUB_TOKEN` — environment variable containing the DoltHub API token
- `P1_API_URL` — defaults to `http://192.168.1.12/api/v1/data`, overridable via environment variable
- `DOLTHUB_OWNER` — defaults to `thomasdekeyser`
- `DOLTHUB_REPO` — defaults to `energy_inside`

## Dependencies

- Python 3 (available on Raspberry Pi OS)
- `uv` — Python package manager (handles venv creation and dependency resolution)
- `requests` library

No `dolt` CLI installation required.

## Deployment

1. Create the `readings` table via the DoltHub web SQL console
2. Install `uv`: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. Clone the project repo to the RPi
4. Install dependencies: `uv sync`
5. Set `DOLTHUB_TOKEN` environment variable
6. Add cron entry: `*/5 * * * * DOLTHUB_TOKEN=<token> cd /home/pi/energy_inside && uv run python collect.py >> /home/pi/energy_inside/collect.log 2>&1`

## Error Handling

- **P1 meter unreachable**: Log error and exit. Cron retries in 5 minutes.
- **DoltHub API unreachable or write fails**: Log error and exit. Cron retries in 5 minutes.
- **Duplicate timestamp**: Use `REPLACE INTO` so that if a reading with the same timestamp already exists, it gets overwritten with the latest values.

## Project Structure

```
energy_inside/
├── collect.py          # Main polling script
├── pyproject.toml      # Project metadata and dependencies (uv)
└── README.md           # Setup instructions for RPi
```

## Future Work (out of scope)

- Static HTML dashboard querying DoltHub read API
