import asyncio
import subprocess
from time import sleep

from playwright.async_api import async_playwright, Playwright
from trafilatura import extract

from summary_bot.settings import (
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
      playwright.browser = 'firefox'
      firefox = playwright.firefox
      browser = await firefox.launch()
      context = await browser.new_context()
      page = await context.new_page()
      await page.goto(url)
      # time.sleep(7)
      content = await page.content()
    # Extract content from the HTML page
    article = extract(content, favor_recall=True, include_comments=False)

    # Close the page and the browser
    await page.close()
    await browser.close()
    return article
