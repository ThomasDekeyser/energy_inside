# Energy Inside — P1 Meter Data Collector

Polls a HomeWizard P1 meter every 5 minutes and stores energy readings in DoltHub.

## Prerequisites

- Raspberry Pi on the same network as the P1 meter
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- DoltHub account with API token

## Setup

1. Create the `readings` table on DoltHub. Go to your repository's SQL console at https://www.dolthub.com/repositories/thomasdekeyser/energy_inside and run:

```sql
CREATE TABLE IF NOT EXISTS readings (
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
);
```

2. Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Clone and install on the Raspberry Pi:

```bash
git clone <repo-url> ~/energy_inside
cd ~/energy_inside
uv sync
```

4. Set your DoltHub token:

```bash
export DOLTHUB_TOKEN=your_token_here
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
