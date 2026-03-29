"""Daily battery simulation: compute savings for different battery sizes."""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone

from energy_inside.dolthub import DoltHubClient, DoltHubError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

DOLTHUB_TOKEN = os.environ.get("DOLTHUB_TOKEN", "")
DOLTHUB_OWNER = os.environ.get("DOLTHUB_OWNER", "thomasdekeyser")
DOLTHUB_REPO = os.environ.get("DOLTHUB_REPO", "energy_inside")

BATTERY_SIZES = [2.7, 5.0, 5.4, 8.1, 10.0, 15.0]
CHARGE_EFFICIENCY = 0.9
DISCHARGE_EFFICIENCY = 0.89


def simulate_battery(rows, capacity):
    """Simulate a battery over a day's readings.

    Returns dict with total_import, total_export, grid_import, grid_export,
    import_saved, export_avoided.
    """
    battery = 0.0
    total_import = 0.0
    total_export = 0.0
    grid_import = 0.0
    grid_export = 0.0

    for i in range(1, len(rows)):
        imp = float(rows[i]["total_power_import_kwh"]) - float(rows[i - 1]["total_power_import_kwh"])
        exp = float(rows[i]["total_power_export_kwh"]) - float(rows[i - 1]["total_power_export_kwh"])

        total_import += imp
        total_export += exp

        if exp > 0:
            # Excess solar: charge battery
            can_store = (capacity - battery) / CHARGE_EFFICIENCY
            charged = min(exp, can_store)
            battery += charged * CHARGE_EFFICIENCY
            grid_export += exp - charged
        elif imp > 0:
            # Consuming: discharge battery
            can_deliver = battery * DISCHARGE_EFFICIENCY
            discharged = min(imp, can_deliver)
            battery -= discharged / DISCHARGE_EFFICIENCY
            grid_import += imp - discharged

    return {
        "total_import": round(total_import, 3),
        "total_export": round(total_export, 3),
        "grid_import": round(grid_import, 3),
        "grid_export": round(grid_export, 3),
        "import_saved": round(total_import - grid_import, 3),
        "export_avoided": round(total_export - grid_export, 3),
    }


def main():
    if not DOLTHUB_TOKEN:
        logger.error("DOLTHUB_TOKEN environment variable is not set")
        sys.exit(1)

    client = DoltHubClient(
        token=DOLTHUB_TOKEN, owner=DOLTHUB_OWNER, repo=DOLTHUB_REPO
    )

    # Simulate yesterday (CET)
    now_utc = datetime.now(timezone.utc)
    # Yesterday in CET: subtract 1 day, get the date part
    yesterday_cet = (now_utc + timedelta(hours=1) - timedelta(days=1)).strftime("%Y-%m-%d")

    # UTC range for yesterday CET
    start = datetime.strptime(yesterday_cet + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    start_utc = (start - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    end_utc = (start + timedelta(hours=23, minutes=59, seconds=59) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

    logger.info("Fetching readings for %s (CET)", yesterday_cet)
    rows = client.execute_read(
        f"SELECT timestamp, total_power_import_kwh, total_power_export_kwh "
        f"FROM readings WHERE timestamp >= '{start_utc}' AND timestamp <= '{end_utc}' "
        f"ORDER BY timestamp"
    )

    if len(rows) < 2:
        logger.warning("Not enough readings for %s, skipping", yesterday_cet)
        sys.exit(0)

    logger.info("Got %d readings, simulating %d battery sizes", len(rows), len(BATTERY_SIZES))

    values = []
    for size in BATTERY_SIZES:
        result = simulate_battery(rows, size)
        values.append(
            f"('{yesterday_cet}', {size}, {result['import_saved']}, "
            f"{result['export_avoided']}, {result['total_import']}, "
            f"{result['total_export']}, {result['grid_import']}, "
            f"{result['grid_export']})"
        )
        logger.info(
            "  %.1f kWh: import saved %.3f kWh, export avoided %.3f kWh",
            size, result["import_saved"], result["export_avoided"],
        )

    sql = (
        "REPLACE INTO battery_simulations "
        "(date, battery_size_kwh, import_saved_kwh, export_avoided_kwh, "
        "total_import_kwh, total_export_kwh, grid_import_kwh, grid_export_kwh) "
        "VALUES " + ", ".join(values)
    )

    client.execute_write(sql)
    logger.info("Results written to battery_simulations")


if __name__ == "__main__":
    try:
        main()
    except DoltHubError as e:
        logger.error("DoltHub error: %s", e)
        sys.exit(1)
