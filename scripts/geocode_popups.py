#!/usr/bin/env python
"""
Batch geocoding script for existing popup stores.
Geocodes all popups that have addresses but no coordinates.

Usage:
    python scripts/geocode_popups.py
    python scripts/geocode_popups.py --dry-run
    python scripts/geocode_popups.py --force  # Re-geocode all addresses
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.db.sqlite.popup_store import get_popup_db
from src.tools.naver.geocoding import geocode_address, batch_geocode_addresses

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def geocode_all_popups(dry_run: bool = False, force: bool = False) -> dict:
    """
    Geocode all popup stores that need coordinates.

    Args:
        dry_run: If True, only show what would be done without making changes
        force: If True, re-geocode all popups even if they have coordinates

    Returns:
        Dictionary with statistics
    """
    stats = {
        "total": 0,
        "needs_geocoding": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
    }

    # Check API credentials
    if not settings.naver_map_client_id or not settings.naver_map_client_secret:
        logger.error("Naver Map API credentials not configured.")
        logger.error("Set NAVER_MAP_CLIENT_ID and NAVER_MAP_CLIENT_SECRET in .env")
        return stats

    db = await get_popup_db()

    # Get all popups
    popups = await db.get_all_popups()
    stats["total"] = len(popups)
    logger.info(f"Found {len(popups)} popup stores in database")

    for popup in popups:
        # Skip if no address
        if not popup.address:
            logger.debug(f"Skipping {popup.name}: No address")
            stats["skipped"] += 1
            continue

        # Skip if already has coordinates (unless force)
        if popup.coordinates and not force:
            logger.debug(f"Skipping {popup.name}: Already has coordinates")
            stats["skipped"] += 1
            continue

        stats["needs_geocoding"] += 1

        if dry_run:
            logger.info(f"[DRY RUN] Would geocode: {popup.name} ({popup.address})")
            continue

        # Geocode the address
        try:
            result = await geocode_address(popup.address)

            if result:
                # Update popup with coordinates
                popup.coordinates = (result.longitude, result.latitude)
                await db.update_popup(popup)

                stats["success"] += 1
                logger.info(
                    f"Geocoded: {popup.name} -> "
                    f"({result.longitude:.6f}, {result.latitude:.6f})"
                )
            else:
                stats["failed"] += 1
                logger.warning(f"No results for: {popup.name} ({popup.address})")

            # Rate limiting - avoid hitting API too fast
            await asyncio.sleep(0.5)

        except Exception as e:
            stats["failed"] += 1
            logger.error(f"Error geocoding {popup.name}: {e}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Batch geocode popup store addresses"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-geocode all addresses, even if coordinates exist",
    )
    args = parser.parse_args()

    logger.info("Starting batch geocoding...")
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    if args.force:
        logger.info("FORCE MODE - Will re-geocode existing coordinates")

    stats = asyncio.run(geocode_all_popups(dry_run=args.dry_run, force=args.force))

    # Print summary
    print("\n" + "=" * 50)
    print("GEOCODING SUMMARY")
    print("=" * 50)
    print(f"Total popups:      {stats['total']}")
    print(f"Needed geocoding:  {stats['needs_geocoding']}")
    print(f"Successfully done: {stats['success']}")
    print(f"Failed:            {stats['failed']}")
    print(f"Skipped:           {stats['skipped']}")
    print("=" * 50)

    if stats["failed"] > 0:
        print("\nSome geocoding failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
