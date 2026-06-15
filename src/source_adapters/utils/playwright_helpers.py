"""
Playwright helper utilities (common reusable functions).
"""

from playwright.async_api import Browser, Page
from typing import Optional
import asyncio


async def create_page(browser: Browser) -> Page:
    """Create a new browser page with default settings."""
    return await browser.new_page()


async def safe_goto(page: Page, url: str, timeout_ms: int = 30000) -> bool:
    """
    Safely navigate to URL with error handling.
    
    Args:
        page: Playwright page object
        url: Target URL
        timeout_ms: Timeout in milliseconds
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        await asyncio.wait_for(
            page.goto(url, wait_until='domcontentloaded'),
            timeout=timeout_ms / 1000
        )
        return True
    except asyncio.TimeoutError:
        print(f"[WARN] Page goto timeout: {url}")
        return False
    except Exception as e:
        print(f"[WARN] Page goto failed: {e}")
        return False


async def safe_wait_for_selector(
    page: Page,
    selector: str,
    timeout_ms: int = 10000
) -> bool:
    """
    Safely wait for CSS selector with error handling.
    
    Args:
        page: Playwright page object
        selector: CSS selector
        timeout_ms: Timeout in milliseconds
    
    Returns:
        bool: True if element found, False otherwise
    """
    try:
        await page.wait_for_selector(selector, timeout=timeout_ms)
        return True
    except asyncio.TimeoutError:
        print(f"[WARN] Selector timeout: {selector}")
        return False
    except Exception as e:
        print(f"[WARN] Wait for selector failed: {e}")
        return False
