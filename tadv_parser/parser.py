import gc
import re

from base_parser import BaseParser
from bs4 import BeautifulSoup
from database import Passport, Project, Company, Product
from datetime import datetime
from shared import should_stop
from playwright._impl._api_types import TimeoutError


def clean_url_string(s):
    s = s.replace(' ', '_')

    # Убираем все символы, которые не подходят для URL (оставляем только буквы, цифры, некоторые специальные символы и '+')
    s = re.sub(r'[^a-zA-Z0-9\-_\.+а-яА-ЯёЁ]', '', s)

    return s


class TadViserParser(BaseParser):

    def __init__(self, browser):
        super().__init__(browser)

        self.company_name = ""
        self.resume_head = "https://tadviser.ru/index.php/Компания:"

    async def parse(self, company_name, company_url=None):
        print("START PARSE TV")
        page = await self.get_new_page()
        self.company_name = company_name
        try:
            if company_url is None:
                company_url = self.resume_head + clean_url_string(company_name)

            html_content = await self.get_page_content(company_url, page)
            if html_content is not None:
                print("PARSE URL", company_url)

                soup = BeautifulSoup(html_content, 'html.parser')

                company_name_block = soup.find("h1", class_="company_name")
                if company_name_block:
                    actual_name = company_name_block.find("span", class_="mw-headline").text
                else:
                    actual_name = ""

                # Находим блок company_left
                company_left_block = soup.find("div", class_="company_left")
                if company_left_block is not None:
                    # Находим все ссылки, начинающиеся с "Категория:"
                    category_links = company_left_block.find_all('a', title=lambda x: x and x.startswith("Категория:"))

                    # Извлекаем текст из этих ссылок и объединяем их через запятую
                    city = ', '.join([link.text for link in category_links])
                else:
                    city = ""

                # Добавляем компанию в таблицу Company
                if company_name:
                    company, created = Company.get_or_create(name=company_name,
                                                             defaults={'website': "", 'city': city,
                                                                       'actual_name': actual_name, 'url': company_url})
                    if not created:
                        if actual_name:
                            company.actual_name = actual_name
                        if city:
                            company.city = city
                        company.save()

                await self.parse_passport(page, soup)
                await self.parse_project(page, soup)
                await self.parse_product(page, soup)
        except Exception as e:
            print("TADV parser: ", e)

        await self.close(page)

        gc.collect()

    async def find_all_companies(self, page, industry_name: str) -> list:
        base_url = f"https://www.tadviser.ru/index.php/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:{clean_url_string(industry_name)}?ptype=comp_otr"
        current_page = 0
        companies = []

        while True:  # Continue until there are no more pages
            url = f"{base_url}&page={current_page}"
            if await self.get_page_content(url, page) is None:
                break

            # Ожидание загрузки элемента с компаниями
            try:
                await page.wait_for_selector(".cwiki_table")
            except TimeoutError:
                print("No company for industry")
                return []

            # Получение содержимого страницы
            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')

            # Извлечение таблицы
            table = soup.find('table', class_='cwiki_table')

            # Извлечение строк компаний из таблицы
            company_rows = table.find_all('tr')[1:]  # Пропускаем строку заголовка

            for row in company_rows:
                anchor = row.find('a')
                if anchor:
                    company = {}
                    company["name"] = anchor.text
                    dirty_url = "/".join(page.url.split("/")[:3]) + anchor.get('href')
                    company["url"] = dirty_url.split("?")[0]
                    companies.append(company)

            # Проверка на наличие кнопки "следующая страница" или аналогичного элемента для пагинации
            next_button = await page.query_selector(".next_button_selector")  # Замените на правильный селектор
            if not next_button:
                break

            current_page += 1

            if should_stop.is_set():
                return []

        return companies

    async def parse_passport(self, page, soup):
        print("PARSE PASSPORT")

        # Находим div с атрибутом name="passport"
        passport_div = soup.find('div', {'name': 'pasport'})

        if not passport_div:
            print("No passport div found.")
            return

        # Ищем table, который имеет того же родителя, что и div
        parent = passport_div.find_parent()
        passport_table = parent.find('table') if parent else None

        if not passport_table:
            print("No sibling table for passport div found.")
            return

        rows = passport_table.find('tbody').find_all('tr')
        for row in rows:
            columns = row.find_all('td')

            if not len(columns) == 5:
                return

            # Извлекаем href из columns[0]
            a_tag = columns[0].find('a')
            if a_tag:
                dirty_url = "/".join(page.url.split("/")[:3]) + a_tag['href']
                project_href = dirty_url.split("?")[0]
            else:
                project_href = None

            print("PASS HREF", project_href)

            passport_data = {
                "project_name": project_href,
                "integrator": columns[1].text.strip(),
                "product": columns[2].text.strip(),
                "technology": columns[3].text.strip()
            }

            # Save to Passport database table
            passport_entry = Passport.get_or_none(Passport.project_name == passport_data['project_name'])
            if not passport_entry:
                passport_entry = Passport(**passport_data)
            else:
                for key, value in passport_data.items():
                    setattr(passport_entry, key, value)

            try:
                update_date = datetime.strptime(columns[4].text.strip(), '%Y')
            except ValueError:
                update_date = None

            print("DATA", update_date)

            # Сохраняем данные паспорта в базе данных
            passport_entry.updated_date = update_date

            main_name = self.find_main_company_name(self.company_name)
            company, created = Company.get_or_create(name=self.company_name if main_name is None else main_name)
            passport_entry.company = company
            passport_entry.save()

            if should_stop.is_set():
                return

    async def parse_project(self, page, soup):
        print("PARSE PROJECT")

        # Находим div с name="project" и у его родителя ищем table без параметров
        project_div = soup.find('div', {'name': 'project'})

        if not project_div:
            print("No project div found.")
            return

        # Ищем table, который имеет того же родителя, что и div
        parent = project_div.find_parent()
        project_table = parent.find('table') if parent else None

        rows = project_table.find('tbody').find_all('tr')
        for row in rows:
            columns = row.find_all('td')

            if not len(columns) == 5:
                return

            # Извлекаем href из columns[0]
            a_tag = columns[4].find('a')
            if a_tag:
                dirty_url = "/".join(page.url.split("/")[:3]) + a_tag['href']
                project_href = dirty_url.split("?")[0]
            else:
                project_href = None

            project_data = {
                "customer": columns[0].text.strip(),
                "product": columns[1].text.strip(),
                "technology": columns[2].text.strip(),
                "project_description": project_href
            }

            # Save to Project database table
            project_entry = Project.get_or_none(Project.project_description == project_data['project_description'])
            if not project_entry:
                project_entry = Project(**project_data)
            else:
                for key, value in project_data.items():
                    setattr(project_entry, key, value)

            try:
                update_date = datetime.strptime(columns[3].text.strip(), '%Y.%m')
            except ValueError:
                update_date = None

            print("DATA", update_date)

            # Сохраняем данные паспорта в базе данных
            project_entry.updated_date = update_date

            main_name = self.find_main_company_name(self.company_name)
            company, created = Company.get_or_create(name=self.company_name if main_name is None else main_name)
            project_entry.company = company
            project_entry.save()

            if should_stop.is_set():
                return

    async def parse_product(self, page, soup):
        print("PARSE PRODUCT")

        # Находим div с name="project" и у его родителя ищем table без параметров
        product_div = soup.find('div', {'name': 'product'})

        if not product_div:
            print("No project div found.")
            return

        # Ищем table, который имеет того же родителя, что и div
        parent = product_div.find_parent()
        product_table = parent.find('table') if parent else None

        rows = product_table.find('tbody').find_all('tr')
        for row in rows:
            columns = row.find_all('td')

            if not len(columns) == 3:
                return

            # Извлекаем href из columns[0]
            a_tag = columns[0].find('a')
            if a_tag:
                dirty_url = "/".join(page.url.split("/")[:3]) + a_tag['href']
                product_href = dirty_url.split("?")[0]
            else:
                product_href = None

            product_data = {
                "name": columns[0].text.strip(),
                "technology": columns[1].text.strip(),
                "count": columns[2].text.strip(),
                "href": product_href
            }

            # Save to Project database table
            product_entry = Product.get_or_none(Product.href == product_data['href'])
            if not product_entry:
                product_entry = Product(**product_data)
            else:
                for key, value in product_data.items():
                    setattr(product_entry, key, value)

            main_name = self.find_main_company_name(self.company_name)
            company, created = Company.get_or_create(name=self.company_name if main_name is None else main_name)
            product_entry.company = company
            product_entry.save()

            if should_stop.is_set():
                return
