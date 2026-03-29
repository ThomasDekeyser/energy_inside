"""Daily battery simulation: run server-side SQL for different battery sizes."""

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
CHARGE_EFF = 0.9
DISCHARGE_EFF = 0.89


def build_simulation_sql(start_utc, end_utc, capacity):
    """Build a recursive CTE that simulates a battery and returns summary."""
    return f"""
WITH RECURSIVE
numbered AS (
  SELECT
    timestamp,
    total_power_import_kwh,
    total_power_export_kwh,
    total_power_import_kwh - LAG(total_power_import_kwh) OVER (ORDER BY timestamp) AS import_kwh,
    total_power_export_kwh - LAG(total_power_export_kwh) OVER (ORDER BY timestamp) AS export_kwh,
    ROW_NUMBER() OVER (ORDER BY timestamp) AS rn
  FROM readings
  WHERE timestamp >= '{start_utc}' AND timestamp <= '{end_utc}'
),
sim AS (
  SELECT
    n.rn,
    0.0 AS import_kwh,
    0.0 AS export_kwh,
    0.0 AS battery_kwh,
    0.0 AS grid_import_kwh,
    0.0 AS grid_export_kwh
  FROM numbered n
  WHERE n.rn = 1

  UNION ALL

  SELECT
    n.rn,
    n.import_kwh,
    n.export_kwh,
    CASE
      WHEN n.export_kwh > 0 THEN
        LEAST(s.battery_kwh + n.export_kwh * {CHARGE_EFF}, {capacity})
      WHEN n.import_kwh > 0 THEN
        GREATEST(s.battery_kwh - n.import_kwh / {DISCHARGE_EFF}, 0.0)
      ELSE s.battery_kwh
    END,
    CASE
      WHEN n.import_kwh > 0 THEN
        GREATEST(n.import_kwh - s.battery_kwh * {DISCHARGE_EFF}, 0.0)
      ELSE 0.0
    END,
    CASE
      WHEN n.export_kwh > 0 THEN
        GREATEST(n.export_kwh - ({capacity} - s.battery_kwh) / {CHARGE_EFF}, 0.0)
      ELSE 0.0
    END
  FROM sim s
  JOIN numbered n ON n.rn = s.rn + 1
)
SELECT
  ROUND(SUM(import_kwh), 3) AS total_import_kwh,
  ROUND(SUM(export_kwh), 3) AS total_export_kwh,
  ROUND(SUM(grid_import_kwh), 3) AS grid_import_kwh,
  ROUND(SUM(grid_export_kwh), 3) AS grid_export_kwh,
  ROUND(SUM(import_kwh) - SUM(grid_import_kwh), 3) AS import_saved_kwh,
  ROUND(SUM(export_kwh) - SUM(grid_export_kwh), 3) AS export_avoided_kwh
FROM sim
"""


def main():
    if not DOLTHUB_TOKEN:
        logger.error("DOLTHUB_TOKEN environment variable is not set")
        sys.exit(1)

    client = DoltHubClient(
        token=DOLTHUB_TOKEN, owner=DOLTHUB_OWNER, repo=DOLTHUB_REPO
    )

    # Simulate yesterday (CET)
    now_utc = datetime.now(timezone.utc)
    yesterday_cet = (now_utc + timedelta(hours=1) - timedelta(days=1)).strftime("%Y-%m-%d")

    # UTC range for yesterday CET
    start = datetime.strptime(yesterday_cet + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    start_utc = (start - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    end_utc = (start + timedelta(hours=23, minutes=59, seconds=59) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

    logger.info("Running battery simulations for %s (CET)", yesterday_cet)

    values = []
    for size in BATTERY_SIZES:
        logger.info("  Simulating %.1f kWh battery (server-side)...", size)
        sql = build_simulation_sql(start_utc, end_utc, size)
        rows = client.execute_read(sql)

        if not rows or rows[0].get("total_import_kwh") is None:
            logger.warning("  No results for %.1f kWh, skipping", size)
            continue

        r = rows[0]
        logger.info(
            "  %.1f kWh: import saved %s kWh, export avoided %s kWh",
            size, r["import_saved_kwh"], r["export_avoided_kwh"],
        )

        values.append(
            f"('{yesterday_cet}', {size}, {r['import_saved_kwh']}, "
            f"{r['export_avoided_kwh']}, {r['total_import_kwh']}, "
            f"{r['total_export_kwh']}, {r['grid_import_kwh']}, "
            f"{r['grid_export_kwh']})"
        )

    if not values:
        logger.warning("No simulation results to write")
        sys.exit(0)

    insert_sql = (
        "REPLACE INTO battery_simulations "
        "(date, battery_size_kwh, import_saved_kwh, export_avoided_kwh, "
        "total_import_kwh, total_export_kwh, grid_import_kwh, grid_export_kwh) "
        "VALUES " + ", ".join(values)
    )

    client.execute_write(insert_sql)
    logger.info("Results written to battery_simulations")


if __name__ == "__main__":
    try:
        main()
    except DoltHubError as e:
        logger.error("DoltHub error: %s", e)
        sys.exit(1)
