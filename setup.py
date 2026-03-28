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
