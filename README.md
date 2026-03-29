# Energy Inside — P1 Meter Data Collector & Battery Simulator

Polls a HomeWizard P1 meter every 5 minutes and stores energy readings in DoltHub. Includes a daily battery simulation that estimates savings for different battery sizes.

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

CREATE TABLE IF NOT EXISTS battery_simulations (
    date DATE,
    battery_size_kwh DECIMAL(5,1),
    import_saved_kwh DECIMAL(10,3),
    export_avoided_kwh DECIMAL(10,3),
    total_import_kwh DECIMAL(10,3),
    total_export_kwh DECIMAL(10,3),
    grid_import_kwh DECIMAL(10,3),
    grid_export_kwh DECIMAL(10,3),
    PRIMARY KEY (date, battery_size_kwh)
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

4. Store your DoltHub token in a secure file:

```bash
echo 'export DOLTHUB_TOKEN=your_token_here' > ~/.dolthub_token
chmod 600 ~/.dolthub_token
```

5. Test a single collection:

```bash
. ~/.dolthub_token
uv run python collect.py
```

6. Add cron job for 5-minute polling:

```bash
crontab -e
```

Add these lines:

```
# Collect readings every 5 minutes
*/5 * * * * . /home/thomas/.dolthub_token && cd /home/thomas/energy_inside && /home/thomas/.local/bin/uv run python collect.py >> collect.log 2>&1

# Run battery simulation daily at 00:15 CET
15 23 * * * . /home/thomas/.dolthub_token && cd /home/thomas/energy_inside && /home/thomas/.local/bin/uv run python simulate_battery.py >> simulate.log 2>&1
```

## Battery Simulation

`simulate_battery.py` runs a server-side recursive CTE on DoltHub that simulates a home battery across all collected readings. It computes cumulative import saved and export avoided for each battery size (2.7, 5, 5.4, 8.1, 10, 15 kWh), using 90% charge and 89% discharge efficiency. Results are written to the `battery_simulations` table, stamped with the date the simulation was run.

Run manually:

```bash
. ~/.dolthub_token
uv run python simulate_battery.py
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

```bash
tail -f ~/energy_inside/collect.log
tail -f ~/energy_inside/simulate.log
```
