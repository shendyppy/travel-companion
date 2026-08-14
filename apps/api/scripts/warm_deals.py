"""
Warm the landing page's fare cache.

    python -m scripts.warm_deals              # every warmed origin
    python -m scripts.warm_deals --origin CGK # just one
    python -m scripts.warm_deals --dry-run    # price everything, cache nothing

`/api/deals` deliberately cannot call a flight provider, so without this the rail
stays empty and the frontend falls back to "cek harga" cards. Run it on a
schedule -- Cloud Scheduler hitting a job, or cron -- at something under
`deals.HARD_TTL_SECONDS`.

The cost is spelled out in `src/deals.py`: roughly one provider call per curated
destination per origin. Read that before adding origins.

Note that with an in-memory session store this only warms *that process*, which
is useless for a separate server. Set REDIS_URL for it to mean anything.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from src import catalogue, deals
from src.config import LOG_FORMAT, LOG_LEVEL
from src.session_store import close_session_store, get_session_store

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger("warm_deals")


async def _warm(origins: list[str], dry_run: bool) -> int:
    store = await get_session_store().health_check()
    if store.get("type") == "in_memory" and not dry_run:
        logger.warning(
            "Session store is in-memory: this warms only the current process. "
            "Set REDIS_URL if the API runs separately."
        )

    total = 0
    for origin in origins:
        if dry_run:
            # refresh() writes to the cache, so a dry run has to stop short of it.
            logger.info("[dry-run] would price %d destinations from %s", len(catalogue.destinations()), origin)
            continue

        payload = await deals.refresh(origin)
        count = len(payload["deals"])
        total += count
        logger.info("%s: %d fares cached for %s", origin, count, payload["departure_date"])

    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Warm the /api/deals fare cache.")
    parser.add_argument(
        "--origin",
        action="append",
        metavar="IATA",
        help=f"Origin to warm; repeatable. Defaults to all of {', '.join(deals.ORIGINS)}.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report what would be priced, cache nothing.")
    args = parser.parse_args()

    origins = [deals.normalise_origin(o) for o in (args.origin or deals.ORIGINS)]

    async def run() -> int:
        try:
            return await _warm(origins, args.dry_run)
        finally:
            await close_session_store()

    total = asyncio.run(run())
    if not args.dry_run and total == 0:
        logger.error("Nothing was cached. Check the flight provider credentials.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
