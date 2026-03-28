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
uv run python create_table.py
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
