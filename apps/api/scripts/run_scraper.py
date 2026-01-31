#!/usr/bin/env python3
"""
Script to run the Instagram scraper manually or start the scheduler.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.scheduler import ScrapeScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_once():
    """Run scraper once."""
    scheduler = ScrapeScheduler()
    logger.info("Running scraper once...")
    await scheduler.run_scrape()
    logger.info("Scrape completed.")


async def run_scheduler():
    """Run scraper with scheduler (continuous)."""
    scheduler = ScrapeScheduler()
    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to stop.")

    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Seongsu Popup Scraper - Fetch popup info from Instagram"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run scraper once and exit",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Start scheduler for periodic scraping",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of posts to fetch (default: 20)",
    )

    args = parser.parse_args()

    if args.once:
        asyncio.run(run_once())
    elif args.schedule:
        asyncio.run(run_scheduler())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
