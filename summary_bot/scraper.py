import asyncio
import subprocess
from time import sleep

from playwright.async_api import async_playwright, Playwright
from trafilatura import extract

from settings import (
    FROM_DOCKER,
    HEADERS,
    EXTRA_HTTP_HEADERS,
    WAIT_COND,
    logger,
)


async def extract_article(url: str) -> str:
    # """
    # Extract the article from the URL with Python's Trafilatura library and ~~Ppeteer~~ `playwright`
    # """

    async with async_playwright() as playwright:
      playwright.browser = 'chromium' #'firefox'
      firefox = playwright.chromium #firefox
      #browser = await playwright.firefox.launch(headless=True)
      browser = await firefox.launch()
      context = await browser.new_context(locale='en-US')
      logger.info(f"url: {url}")
      page = await context.new_page()
      await page.goto(url)
      #time.
      #sleep(3)
      content = await page.content()
      
    # Extract content from the HTML page
    article = extract(content, favor_recall=True, include_comments=False)
    logger.info(f"article:\n\n{article[100:600]}\n")

    # Close the page and the browser
    await page.close()
    await browser.close()
    return article
