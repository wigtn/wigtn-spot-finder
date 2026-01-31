"""
Observer Agent runner script.
Starts the background Observer Agent for monitoring and log collection.
"""

import asyncio
import logging
import signal
import sys

from src.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ObserverAgentRunner:
    """Runner for the Observer Agent."""

    def __init__(self):
        self.running = False
        self.agent = None

    async def start(self):
        """Start the Observer Agent."""
        if not settings.observer_agent_enabled:
            logger.warning("Observer Agent is disabled in settings. Exiting.")
            return

        logger.info("Starting Observer Agent...")
        self.running = True

        # Import here to avoid circular imports
        from src.agents.observer_agent import ObserverAgent

        self.agent = ObserverAgent(
            redis_url=settings.redis_url,
            sentry_dsn=settings.sentry_dsn,
            logtail_token=settings.logtail_token,
        )

        try:
            await self.agent.run()
        except Exception as e:
            logger.error(f"Observer Agent error: {e}")
            raise

    async def stop(self):
        """Stop the Observer Agent gracefully."""
        logger.info("Stopping Observer Agent...")
        self.running = False

        if self.agent:
            await self.agent.shutdown()

        logger.info("Observer Agent stopped")


async def main():
    """Main entry point for Observer Agent."""
    runner = ObserverAgentRunner()

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()

    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(runner.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await runner.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await runner.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Observer Agent terminated")
        sys.exit(0)
