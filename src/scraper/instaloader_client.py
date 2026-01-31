"""
Instaloader client for Instagram scraping.
Fetches posts from @seongsu_bible account.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

import instaloader
from instaloader import Post, Profile

from src.config.settings import settings
from src.models.instagram import InstagramPost

logger = logging.getLogger(__name__)


class InstaloaderClient:
    """
    Client for scraping Instagram posts using Instaloader.
    Targets @seongsu_bible account for Seongsu popup information.
    """

    def __init__(
        self,
        target_account: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        """
        Initialize the Instaloader client.

        Args:
            target_account: Instagram account to scrape
            username: Instagram username for authenticated requests
            password: Instagram password for authenticated requests
        """
        self.target_account = target_account or settings.instagram_target_account
        self.username = username or settings.instagram_username
        self.password = password or settings.instagram_password

        self._loader: instaloader.Instaloader | None = None
        self._profile: Profile | None = None

    @property
    def loader(self) -> instaloader.Instaloader:
        """Get or create Instaloader instance."""
        if self._loader is None:
            self._loader = instaloader.Instaloader(
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
                quiet=True,
            )

            # Login if credentials are provided
            if self.username and self.password:
                try:
                    self._loader.login(self.username, self.password)
                    logger.info(f"Logged in as {self.username}")
                except Exception as e:
                    logger.warning(f"Login failed, continuing anonymously: {e}")

        return self._loader

    async def get_profile(self) -> Profile:
        """Get target Instagram profile."""
        if self._profile is None:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_running_loop()
            self._profile = await loop.run_in_executor(
                None,
                Profile.from_username,
                self.loader.context,
                self.target_account,
            )
            logger.info(f"Loaded profile: @{self.target_account}")

        return self._profile

    async def get_recent_posts(self, limit: int = 50) -> list[InstagramPost]:
        """
        Fetch recent posts from target account.

        Args:
            limit: Maximum number of posts to fetch

        Returns:
            List of InstagramPost objects
        """
        profile = await self.get_profile()

        posts: list[InstagramPost] = []
        loop = asyncio.get_running_loop()

        def fetch_posts():
            fetched = []
            for i, post in enumerate(profile.get_posts()):
                if i >= limit:
                    break

                # Extract image URLs
                image_urls = []
                if post.typename == "GraphSidecar":
                    # Multiple images
                    for node in post.get_sidecar_nodes():
                        if not node.is_video:
                            image_urls.append(node.display_url)
                elif not post.is_video:
                    image_urls.append(post.url)

                # Extract hashtags from caption
                hashtags = []
                if post.caption_hashtags:
                    hashtags = list(post.caption_hashtags)

                fetched.append(InstagramPost(
                    shortcode=post.shortcode,
                    caption=post.caption or "",
                    image_urls=image_urls,
                    timestamp=post.date_utc,
                    likes=post.likes,
                    comments_count=post.comments,
                    hashtags=hashtags,
                    location_tag=post.location.name if post.location else None,
                ))

            return fetched

        try:
            posts = await loop.run_in_executor(None, fetch_posts)
            logger.info(f"Fetched {len(posts)} posts from @{self.target_account}")
        except Exception as e:
            logger.error(f"Failed to fetch posts: {e}")
            raise

        return posts

    async def get_post_by_shortcode(self, shortcode: str) -> InstagramPost | None:
        """
        Fetch a single post by shortcode.

        Args:
            shortcode: Instagram post shortcode

        Returns:
            InstagramPost or None if not found
        """
        loop = asyncio.get_running_loop()

        def fetch_post():
            try:
                post = Post.from_shortcode(self.loader.context, shortcode)

                image_urls = []
                if post.typename == "GraphSidecar":
                    for node in post.get_sidecar_nodes():
                        if not node.is_video:
                            image_urls.append(node.display_url)
                elif not post.is_video:
                    image_urls.append(post.url)

                hashtags = list(post.caption_hashtags) if post.caption_hashtags else []

                return InstagramPost(
                    shortcode=post.shortcode,
                    caption=post.caption or "",
                    image_urls=image_urls,
                    timestamp=post.date_utc,
                    likes=post.likes,
                    comments_count=post.comments,
                    hashtags=hashtags,
                    location_tag=post.location.name if post.location else None,
                )
            except Exception as e:
                logger.error(f"Failed to fetch post {shortcode}: {e}")
                return None

        return await loop.run_in_executor(None, fetch_post)

    async def download_post_images(
        self,
        post: InstagramPost,
        output_dir: Path | str,
    ) -> list[Path]:
        """
        Download images from a post.

        Args:
            post: Instagram post
            output_dir: Directory to save images

        Returns:
            List of downloaded image paths
        """
        import httpx

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        downloaded: list[Path] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, url in enumerate(post.image_urls):
                try:
                    response = await client.get(url)
                    response.raise_for_status()

                    # Determine file extension
                    content_type = response.headers.get("content-type", "")
                    ext = ".jpg"
                    if "png" in content_type:
                        ext = ".png"
                    elif "webp" in content_type:
                        ext = ".webp"

                    filename = f"{post.shortcode}_{i}{ext}"
                    filepath = output_path / filename

                    with open(filepath, "wb") as f:
                        f.write(response.content)

                    downloaded.append(filepath)
                    logger.debug(f"Downloaded: {filepath}")

                except Exception as e:
                    logger.warning(f"Failed to download image {url}: {e}")

        return downloaded


# Global instance
_instaloader_client: InstaloaderClient | None = None


def get_instaloader_client() -> InstaloaderClient:
    """Get global Instaloader client instance."""
    global _instaloader_client
    if _instaloader_client is None:
        _instaloader_client = InstaloaderClient()
    return _instaloader_client
