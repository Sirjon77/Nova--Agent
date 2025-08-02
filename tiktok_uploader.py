"""
TikTok Uploader using Browser Automation

Since TikTok doesn't provide a public upload API, this module uses Playwright
to automate the upload process through the web interface.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class TikTokUploader:
    """TikTok upload automation using Playwright."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.page = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def login(self, username: str, password: str) -> bool:
        """Login to TikTok account."""
        try:
            await self.page.goto("https://www.tiktok.com/login")
            await self.page.wait_for_load_state("networkidle")
            
            # Wait for login form and fill credentials
            await self.page.fill('input[name="username"]', username)
            await self.page.fill('input[name="password"]', password)
            await self.page.click('button[type="submit"]')
            
            # Wait for successful login
            await self.page.wait_for_url("https://www.tiktok.com/", timeout=30000)
            logger.info("Successfully logged into TikTok")
            return True
            
        except Exception as e:
            logger.error(f"TikTok login failed: {e}")
            return False
    
    async def upload_video(self, video_path: str, caption: str, 
                          hashtags: Optional[str] = None) -> Dict[str, Any]:
        """Upload video to TikTok."""
        try:
            # Navigate to upload page
            await self.page.goto("https://www.tiktok.com/upload")
            await self.page.wait_for_load_state("networkidle")
            
            # Upload video file
            file_input = await self.page.wait_for_selector('input[type="file"]')
            await file_input.set_input_files(video_path)
            
            # Wait for video to upload
            await self.page.wait_for_selector('.upload-progress', timeout=60000)
            await self.page.wait_for_selector('.upload-progress:not(.uploading)', timeout=120000)
            
            # Add caption
            caption_input = await self.page.wait_for_selector('textarea[placeholder*="caption"]')
            await caption_input.fill(caption)
            
            # Add hashtags if provided
            if hashtags:
                hashtag_input = await self.page.wait_for_selector('input[placeholder*="hashtag"]')
                await hashtag_input.fill(hashtags)
            
            # Set privacy (public by default)
            public_button = await self.page.wait_for_selector('button[data-testid="public"]')
            await public_button.click()
            
            # Submit upload
            submit_button = await self.page.wait_for_selector('button[data-testid="submit"]')
            await submit_button.click()
            
            # Wait for upload completion
            await self.page.wait_for_selector('.upload-success', timeout=60000)
            
            logger.info(f"Successfully uploaded video: {video_path}")
            return {
                "status": "success",
                "video_path": video_path,
                "caption": caption,
                "upload_time": time.time()
            }
            
        except Exception as e:
            logger.error(f"TikTok upload failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "video_path": video_path
            }

async def upload_to_tiktok(video_path: str, caption: str, 
                          username: Optional[str] = None, 
                          password: Optional[str] = None,
                          hashtags: Optional[str] = None) -> Dict[str, Any]:
    """
    Upload video to TikTok using browser automation.
    
    Args:
        video_path: Path to video file
        caption: Video caption text
        username: TikTok username (from env if not provided)
        password: TikTok password (from env if not provided)
        hashtags: Optional hashtags string
        
    Returns:
        Dict with upload status and details
    """
    # Get credentials from environment if not provided
    username = username or os.getenv("TIKTOK_USERNAME")
    password = password or os.getenv("TIKTOK_PASSWORD")
    
    if not username or not password:
        logger.warning("TikTok credentials not provided - using placeholder")
        return {
            "status": "placeholder",
            "message": "TikTok credentials not configured",
            "video_path": video_path,
            "caption": caption
        }
    
    # Validate video file
    if not Path(video_path).exists():
        return {
            "status": "error",
            "error": f"Video file not found: {video_path}"
        }
    
    async with TikTokUploader() as uploader:
        # Login first
        if not await uploader.login(username, password):
            return {
                "status": "error",
                "error": "Failed to login to TikTok"
            }
        
        # Upload video
        return await uploader.upload_video(video_path, caption, hashtags)

# Backward compatibility function
def upload_to_tiktok_sync(video_path: str, caption: str) -> Dict[str, Any]:
    """Synchronous wrapper for TikTok upload."""
    import asyncio
    return asyncio.run(upload_to_tiktok(video_path, caption))
