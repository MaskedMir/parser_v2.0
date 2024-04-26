import time
import random

from playwright_stealth import stealth_async
from database import *
from shared import should_stop


class BaseParser:
    def __init__(self, browser):
        self.browser = browser
        self.should_continue = True

    async def get_page_content(self, url, page):
        tries = 0
        while tries < 10:
            try:
                await page.goto(url, timeout=30000)

                return await page.content()
            except Exception as e:
                print(f"Failed to navigate to {url}. Try {tries + 1}. The error was: {e}")
                time.sleep(random.uniform(1, 5))

            tries += 1

            if should_stop.is_set():
                return None
        return None

    def find_main_company_name(self, parsed_name):
        """Ищет точное совпадение 'основного' имени компании из SearchList."""
        search_company = SearchCompany.select().where(SearchCompany.company_name ** parsed_name).first()
        if search_company:
            return search_company.company_name
        return None

    async def get_new_page(self):
        page = await self.browser.new_page()
        await page.route('**/*.{png,jpg,jpeg}', lambda route, request: route.abort())
        await stealth_async(page)
        return page

    async def parse(self, company_names):
        raise NotImplementedError("Each parser should implement this method")

    async def close(self, page):
        await page.close()
