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
