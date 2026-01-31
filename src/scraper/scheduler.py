"""
Scraping scheduler using APScheduler.
Periodically fetches and parses Instagram posts.
"""

import asyncio
import logging
from datetime import datetime
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.config.settings import settings
from src.db.sqlite.popup_store import PopupStoreDB, get_popup_db
from src.models.instagram import ScrapeLog
from src.scraper.instaloader_client import InstaloaderClient, get_instaloader_client
from src.scraper.parser import InstagramPostParser, get_post_parser
from src.services.memory.embeddings import get_embedding_service
from src.tools.naver.geocoding import geocode_address

logger = logging.getLogger(__name__)


class ScrapeScheduler:
    """
    Scheduler for periodic Instagram scraping.
    Runs scraping job at configured intervals.
    """

    def __init__(
        self,
        interval_hours: int | None = None,
        insta_client: InstaloaderClient | None = None,
        parser: InstagramPostParser | None = None,
        db: PopupStoreDB | None = None,
    ):
        """
        Initialize the scheduler.

        Args:
            interval_hours: Hours between scraping runs
            insta_client: Instagram client
            parser: Post parser
            db: Popup store database
        """
        self.interval_hours = interval_hours or settings.scrape_interval_hours
        self.insta_client = insta_client
        self.parser = parser
        self.db = db

        self._scheduler: AsyncIOScheduler | None = None
        self._is_running = False
        self._on_complete_callbacks: list[Callable] = []

    @property
    def scheduler(self) -> AsyncIOScheduler:
        """Get or create scheduler."""
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler()
        return self._scheduler

    def _get_insta_client(self) -> InstaloaderClient:
        """Get Instagram client."""
        return self.insta_client or get_instaloader_client()

    def _get_parser(self) -> InstagramPostParser:
        """Get post parser."""
        return self.parser or get_post_parser()

    async def _get_db(self) -> PopupStoreDB:
        """Get popup database."""
        if self.db:
            return self.db
        return await get_popup_db()

    def add_completion_callback(self, callback: Callable):
        """Add callback to run after scraping completes."""
        self._on_complete_callbacks.append(callback)

    async def run_scrape(self, limit: int = 50) -> ScrapeLog:
        """
        Run a single scraping cycle.

        Args:
            limit: Maximum posts to fetch

        Returns:
            ScrapeLog with results
        """
        log = ScrapeLog(
            started_at=datetime.utcnow(),
            status="running",
        )

        try:
            logger.info("Starting scrape cycle...")

            insta = self._get_insta_client()
            parser = self._get_parser()
            db = await self._get_db()
            embedding_service = get_embedding_service()

            # Fetch recent posts
            posts = await insta.get_recent_posts(limit=limit)
            log.posts_fetched = len(posts)
            logger.info(f"Fetched {len(posts)} posts")

            # Get existing post IDs to avoid reprocessing
            existing_ids = await db.get_existing_post_ids()

            # Process new posts
            for post in posts:
                if post.shortcode in existing_ids:
                    logger.debug(f"Skipping already processed: {post.shortcode}")
                    continue

                try:
                    # Parse post
                    parsed = await parser.parse_post(post)
                    if not parsed:
                        logger.warning(f"Failed to parse: {post.shortcode}")
                        continue

                    log.posts_parsed += 1

                    # Skip low confidence results
                    if parsed.confidence_score < settings.min_confidence_threshold:
                        logger.debug(
                            f"Low confidence ({parsed.confidence_score:.2f} < "
                            f"{settings.min_confidence_threshold}): {post.shortcode}"
                        )
                        continue

                    # Create popup store
                    popup = await parser.create_popup_from_post(post, parsed)

                    # Geocode address if available and coordinates not set
                    if popup.address and not popup.coordinates:
                        try:
                            geocode_result = await geocode_address(popup.address)
                            if geocode_result:
                                popup.coordinates = (
                                    geocode_result.longitude,
                                    geocode_result.latitude,
                                )
                                logger.info(
                                    f"Geocoded {popup.name}: "
                                    f"({geocode_result.longitude}, {geocode_result.latitude})"
                                )
                        except Exception as e:
                            logger.warning(f"Geocoding failed for {popup.name}: {e}")

                    # Set thumbnail from first image if available
                    if post.image_urls and not popup.thumbnail_url:
                        popup.thumbnail_url = post.image_urls[0]
                        popup.images = post.image_urls

                    # Generate embedding
                    try:
                        search_text = popup.to_search_text()
                        embedding = await embedding_service.embed_text(search_text)
                        popup.embedding_id = popup.id
                    except Exception as e:
                        logger.warning(f"Embedding failed: {e}")
                        embedding = None

                    # Check if popup already exists (by source post)
                    existing = await db.get_popup_by_source_id(post.shortcode)

                    if existing:
                        # Update existing
                        await db.update_popup(popup)
                        log.popups_updated += 1
                        logger.info(f"Updated popup: {popup.name}")
                    else:
                        # Create new
                        await db.create_popup(popup, embedding)
                        log.popups_created += 1
                        logger.info(f"Created popup: {popup.name}")

                    # Mark post as processed
                    await db.mark_post_processed(post.shortcode)

                    # Small delay to avoid rate limiting
                    await asyncio.sleep(settings.scrape_delay_seconds)

                except Exception as e:
                    logger.error(f"Error processing post {post.shortcode}: {e}")
                    continue

            log.status = "completed"
            log.completed_at = datetime.utcnow()

            logger.info(
                f"Scrape completed: {log.posts_parsed} parsed, "
                f"{log.popups_created} created, {log.popups_updated} updated"
            )

        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            log.completed_at = datetime.utcnow()
            logger.error(f"Scrape failed: {e}")

        # Save log
        try:
            db = await self._get_db()
            await db.save_scrape_log(log)
        except Exception as e:
            logger.error(f"Failed to save scrape log: {e}")

        # Run callbacks
        for callback in self._on_complete_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(log)
                else:
                    callback(log)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        return log

    def start(self):
        """Start the scheduler."""
        if self._is_running:
            logger.warning("Scheduler already running")
            return

        self.scheduler.add_job(
            self.run_scrape,
            trigger=IntervalTrigger(hours=self.interval_hours),
            id="instagram_scrape",
            name="Instagram Scrape Job",
            replace_existing=True,
        )

        self.scheduler.start()
        self._is_running = True
        logger.info(f"Scheduler started (interval: {self.interval_hours}h)")

    def stop(self):
        """Stop the scheduler."""
        if self._scheduler and self._is_running:
            self._scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("Scheduler stopped")

    async def run_once(self, limit: int = 50) -> ScrapeLog:
        """
        Run scraping once without scheduling.

        Args:
            limit: Maximum posts to fetch

        Returns:
            ScrapeLog with results
        """
        return await self.run_scrape(limit=limit)


# Global instance
_scheduler: ScrapeScheduler | None = None


def get_scheduler() -> ScrapeScheduler:
    """Get global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ScrapeScheduler()
    return _scheduler
