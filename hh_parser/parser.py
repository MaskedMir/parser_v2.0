import gc
import re
import playwright

from datetime import datetime, date
from base_parser import BaseParser
from bs4 import BeautifulSoup
from database import Resume, Vacancy, Company
from shared import should_stop
from playwright._impl._api_types import TimeoutError


should_continue = True


def clean_url_string(s):
    s = s.replace(' ', '+')

    # Убираем все символы, которые не подходят для URL (оставляем только буквы, цифры, некоторые специальные символы и '+')
    s = re.sub(r'[^a-zA-Z0-9\-_\.+а-яА-ЯёЁ]', '', s)

    return s


def parse_date(date_str):
    # Mapping of month names to their respective numbers
    month_mapping = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }

    # Regex pattern to match date formats
    pattern_1 = r"(\d+)\s+(\w+)\s+(\d{4})"
    pattern_2 = r"(\d+)\s+(\w+)\s+в\s+(\d{2}:\d{2})"

    match_1 = re.search(pattern_1, date_str)
    match_2 = re.search(pattern_2, date_str)

    if match_1:
        day = int(match_1.group(1))
        month = month_mapping[match_1.group(2)]
        year = int(match_1.group(3))
        return date(year, month, day)
    elif match_2:
        day = int(match_2.group(1))
        month = month_mapping[match_2.group(2)]
        time = match_2.group(3)
        hour, minute = map(int, time.split(":"))
        # Since year is not provided, assuming it as the current year
        year = datetime.now().year
        return datetime(year, month, day, hour, minute)
    else:
        return None


class HeadHunterParser(BaseParser):

    def __init__(self, browser):
        super().__init__(browser)

        self.company_name = ""
        self.resume_head = "https://hh.ru/search/resume?text="

        self.resume_tail = "&logic=phrase&pos=workplace_organization&exp_period=all_time&exp_company_size=any" \
                           "&exp_industry=any&area=1&relocation=living_or_relocation&age_from=&age_to=&gender=unknown" \
                           "&salary_from=&salary_to=&currency_code=RUR&order_by=relevance&search_period=0" \
                           "&items_on_page=100&no_magic=false"

    async def parse(self, company_name, company_url=None):
        print("START PARSE HH")
        page = await self.get_new_page()
        self.company_name = company_name

        print("RUN LOOP")
        try:
            result_text = ""
            print("PARSER COMPANY", company_name, clean_url_string(company_name), company_url)

            resume_url = self.resume_head + clean_url_string(company_name) + self.resume_tail

            if company_url is None:
                company_url = await self.find_company_url(page, company_name)

            print("URL", company_url)

            if company_url:
                await self.parse_company_url(company_url, page)
            await self.parse_resumes(resume_url, page)

        except Exception as e:
            print("HH parser: ", e)

        await self.close(page)

        gc.collect()


    async def find_company_url(self, page, company_name: str) -> str:
        base_url = f"https://hh.ru/employers_list?query={clean_url_string(company_name)}"
        current_page = 0

        while True:
            url = f"{base_url}&page={current_page}"
            if await self.get_page_content(url, page) is None:
                return ""

            # Ожидание загрузки элемента с компаниями
            try:
                await page.wait_for_selector("[data-qa='employers-list-company-list']")
            except TimeoutError:
                print("No company for industry")
                return ""

            # Получение всех дочерних div элементов
            divs = await page.query_selector_all("[data-qa='employers-list-company-list'] > div")

            for div in divs:
                # Находим тег <a> внутри каждого div
                link_element = await div.query_selector("a")

                # Проверяем текст внутри тега <a>
                link_text = await link_element.text_content()

                if link_text == company_name:
                    full_url = "/".join(page.url.split("/")[:3]) + await link_element.get_attribute("href")
                    clean_url = full_url.split("?")[0]
                    return clean_url

            # Проверка на наличие кнопки "следующая страница" или аналогичного элемента для пагинации
            next_button = await page.query_selector("[data-qa='pager-next']")
            if not next_button:
                break

            current_page += 1

            if should_stop.is_set():
                return ""

        # Если компания не найдена на всех страницах, возвращаем None
        return ""

    async def find_company_link_by_keyword(self, page, keyword: str):
        base_url = "https://hh.ru/employers_company?area=113"

        html_contnet = await self.get_page_content(base_url, page)
        if html_contnet is None:
            return None

        soup = BeautifulSoup(html_contnet, 'html.parser')
        content_block = soup.find("div", class_="employers-company__content")

        if not content_block:
            print("No employers-company__content block found.")
            return None

        for link_element in content_block.find_all("a"):
            text_content = link_element.text
            if keyword in text_content:
                return "/".join(page.url.split("/")[:3]) + link_element["href"]

        print(f"No link found for keyword: {keyword}")
        return None

    async def find_all_companies(self, page, company_name: str) -> list:
        list_url = await self.find_company_link_by_keyword(page, company_name)
        if not list_url:
            return []

        if await self.get_page_content(list_url, page) is None:
            return []

        companies = []
        base_url = "/".join(page.url.split("/")[:3])

        while True:
            try:
                await page.wait_for_selector(".content")
            except TimeoutError:
                print("No company for industry")
                return companies

            html_content = await page.content()

            print("CONTENT", len(html_content), page.url)

            if html_content is None:
                return companies

            soup = BeautifulSoup(html_content, 'html.parser')
            content_block = soup.find("div", class_="content")
            company_list_block = content_block.find("div", class_="employers-company__list")

            for link_element in company_list_block.find_all("a"):
                dirty_url = base_url + link_element["href"]
                clean_url = dirty_url.split("?")[0]

                company = {
                    "name": link_element.text.strip(),
                    "url": clean_url
                }

                print("FIND COMPANY", company["name"])

                companies.append(company)

            next_button = soup.find("a", class_="HH-Pager-Controls-Next")
            if not next_button:
                break

            # Переходим на следующую страницу
            await page.click("a.HH-Pager-Controls-Next")

            if should_stop.is_set():
                return []

        return companies

    async def parse_vacancy_url(self, url, page):
        print("PARSE VACANCY", url)

        content = await self.get_page_content(url, page)
        if content is None:
            return None

        soup = BeautifulSoup(content, 'html.parser')

        # Extract the job title and description
        title_element = soup.find('h1', {'data-qa': 'vacancy-title'})
        title_text = title_element.text if title_element else None
        description_element = soup.find('div', {'data-qa': 'vacancy-description'})
        description_text = description_element.get_text(separator=' ', strip=True) if description_element else None

        date_element = soup.find('p', class_='vacancy-creation-time-redesigned')
        publication_date = None
        if date_element:
            date_span = date_element.find('span')
            if date_span:
                date_str = date_span.text.strip()
                parsed_date = parse_date(date_str)
                if parsed_date:
                    publication_date = parsed_date  # Use the parsed date object instead of the string

        clean_url = url.split("?")[0]

        # Return the vacancy data
        vacancy_data = {
            "url": clean_url,
            "title": title_text,
            "description": description_text,
            "publication_date": publication_date,
            "source": "hh; вакансия"
        }

        return vacancy_data

    async def parse_company_url(self, url, page):
        global should_continue

        print("PARSE COMPANY", url)
        html_content = await self.get_page_content(url, page)
        if html_content is None:
            return

        # Получаем содержимое страницы и парсим его с помощью BeautifulSoup
        title_soup = BeautifulSoup(html_content, 'html.parser')

        # Находим название компании, сайт и город
        company_name_elem = title_soup.find('span', {'data-qa': 'company-header-title-name'})
        if company_name_elem is None:
            actual_name = self.company_name
        else:
            actual_name = company_name_elem.text if company_name_elem else None

        company_website_elem = title_soup.find('button', {'data-qa': 'sidebar-company-site'})
        if company_website_elem is None:
            company_website = ""
        else:
            company_website = company_website_elem.span.text if company_website_elem and company_website_elem.span else None

        company_city_elem = title_soup.find('div', {'class': 'employer-sidebar-content'})
        if company_city_elem is None:
            company_city = ""
        else:
            company_city_block = company_city_elem.find('div', class_='employer-sidebar-block')
            if company_city_block is None:
                company_city = ""
            else:
                company_city = company_city_block.text if company_city_block else None

        print("company_city", company_city)

        # Добавляем компанию в таблицу Company
        company, created = Company.get_or_create(name=self.company_name,
                                                 defaults={'website': company_website, 'city': company_city,
                                                           'actual_name': actual_name, 'url': url})
        if not created:
            if actual_name:
                company.actual_name = actual_name
            if company_website:
                company.website = company_website
            if company_city:
                company.city = company_city
            company.save()

        # Находим все элементы с нужным атрибутом data-qa
        prof_role_elements = await page.query_selector_all('div[data-qa^="vacancies-in-prof-role"]')

        if len(prof_role_elements):
            for element_handle in prof_role_elements:
                print("CHECK VAC HANDLE")
                if not should_continue:
                    return

                data_qa_value = await element_handle.get_attribute("data-qa")
                # Нажимаем на кнопку внутри текущего элемента
                print("GET HANDLE QUERY")
                button = await element_handle.query_selector('button[data-qa="vacancies-in-prof-role-switch"]')
                if button:
                    # Создаем контекст ожидания навигации
                    print("BUTTON CLICK!!!")
                    await button.click()

                    await page.wait_for_selector(f'div[data-qa="{data_qa_value}"] div.vacancy-list-item',
                                                 timeout=60000)

                    more_button = await page.query_selector('button[data-qa="vacancies-more-button"]')
                    if more_button:
                        await more_button.click()
                        await page.wait_for_timeout(10000)

                    print("GOT SELECTOR!!!")

                    # # Продолжаем парсинг после обновления содержимого
                    inner_html = await element_handle.inner_html()
                    soup = BeautifulSoup(inner_html, 'html.parser')

                    # Находим все элементы с классом "vacancy-list-item" внутри найденного элемента
                    vacancy_items = soup.find_all('div', class_='vacancy-list-item')

                    print("VAC COUNT", len(vacancy_items))

                    local_page = await self.get_new_page()
                    for item in vacancy_items:
                        if not should_continue:
                            return

                        # Находим элемент с атрибутом data-qa="vacancy-serp__vacancy-title" и извлекаем значение атрибута href
                        vacancy_title = item.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})
                        if vacancy_title:
                            vac_data = await self.parse_vacancy_url(vacancy_title['href'], local_page)

                            if vac_data is None:
                                continue

                            print("VACANCY GET")

                            vacancy = Vacancy.get_or_none(Vacancy.url == vac_data['url'])
                            if not vacancy:
                                main_name = self.find_main_company_name(self.company_name)
                                company, created = Company.get_or_create(name=self.company_name if main_name is None else main_name)

                                vac_data["company"] = company
                                vacancy = Vacancy(**vac_data)
                                vacancy.save()

                    await local_page.close()

                if should_stop.is_set():
                    return {}
        else:
            print("ONLY VAC LIST!!!")

            vacancy_items = title_soup.find_all('div', class_='vacancy-list-item')

            print("VAC COUNT", len(vacancy_items))

            local_page = await self.get_new_page()
            for item in vacancy_items:
                if not should_continue:
                    return

                # Находим элемент с атрибутом data-qa="vacancy-serp__vacancy-title" и извлекаем значение атрибута href
                vacancy_title = item.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})
                if vacancy_title:
                    vac_data = await self.parse_vacancy_url(vacancy_title['href'], local_page)

                    if vac_data is None:
                        continue

                    print("VACANCY GET")

                    vacancy = Vacancy.get_or_none(Vacancy.url == vac_data['url'])
                    if not vacancy:
                        main_name = self.find_main_company_name(self.company_name)
                        company, created = Company.get_or_create(
                            name=self.company_name if main_name is None else main_name)

                        vac_data["company"] = company
                        vacancy = Vacancy(**vac_data)
                        vacancy.save()

            await local_page.close()

        return

    async def parse_resumes(self, url, page):
        global should_continue
        print("PARSE RESUMES")

        print("GO TO PAGE", url)

        if await self.get_page_content(url, page) is None:
            return

        print("PAGE GET!!")

        # Получаем все страницы для текущего имени
        all_pages = await self.get_pages(page)

        print(all_pages)

        # Обходим каждую страницу
        for page_url in all_pages:
            if not should_continue:
                return

            if await self.get_page_content(page_url, page) is None:
                continue

            inner_html = await page.content()
            soup = BeautifulSoup(inner_html, 'html.parser')

            # Находим блок с классом 'resume-serp-content'
            resume_serp_content = soup.find('main', class_='resume-serp-content')

            # Если блок найден, ищем в нем все элементы с классом 'serp-item'
            if resume_serp_content:
                print("FIND resume-serp-content")
                serp_items = resume_serp_content.find_all('div', class_='serp-item')

                # Для каждого элемента 'serp-item' ищем 'serp-item__title' и извлекаем значение атрибута 'href'
                local_page = await self.get_new_page()

                print("find serp items", len(serp_items))

                # Извлекаем базовый URL (до первого слеша после домена)
                base_url = "/".join(page.url.split("/")[:3])
                for item in serp_items:
                    title = item.find('a', class_='serp-item__title')
                    print("CHECK RESUME HREF", title)
                    if title and 'href' in title.attrs:
                        dirty_url = base_url + title['href']
                        full_url = dirty_url.split("?")[0]

                        print("CALL PARSE RESUME")
                        resume_data = await self.parse_resume(full_url, local_page)

                        if resume_data is None:
                            continue

                        # Extract the publication date
                        date_element = item.find('span', class_='date--cHInIjOdiyfDqTabYRkp')
                        if date_element:
                            date_str = date_element.text.strip()
                            parsed_date = parse_date(date_str)
                            if parsed_date:
                                # Convert the parsed date to a string format
                                if isinstance(parsed_date, datetime):
                                    formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M')
                                else:
                                    formatted_date = parsed_date.strftime('%Y-%m-%d')
                                resume_data['publication_date'] = formatted_date

                        # Save the data to the database
                        resume = Resume.get_or_none(Resume.url == full_url)
                        if not resume:
                            resume = Resume(url=full_url)
                        for key, value in resume_data.items():
                            if key in Resume._meta.fields:
                                setattr(resume, key, value)

                        main_name = self.find_main_company_name(self.company_name)
                        company, created = Company.get_or_create(name=self.company_name if main_name is None else main_name)
                        resume.company = company
                        resume.save()

                    if should_stop.is_set():
                        return

                await local_page.close()

            if should_stop.is_set():
                return

    def flatten_array(self, arr):
        flattened = []

        def recursive_flatten(sub_arr):
            if isinstance(sub_arr, list):
                for item in sub_arr:
                    recursive_flatten(item)
            elif isinstance(sub_arr, dict):
                for value in sub_arr.values():
                    recursive_flatten(value)
            else:
                flattened.append(sub_arr)

        recursive_flatten(arr)
        return '.'.join(flattened)

    async def parse_resume(self, url, page):
        print("PARSER RESUME", url)
        if await self.get_page_content(url, page) is None:
            return None

        html_content = await page.content()

        soup = BeautifulSoup(html_content, 'html.parser')
        data = {}

        # Извлечение позиции
        position = soup.find('span', {'data-qa': 'resume-block-title-position'})
        if position:
            data['position'] = position.text.strip()

        # Извлечение зарплаты
        salary = soup.find('span', {'data-qa': 'resume-block-salary'})
        if salary:
            data['salary'] = salary.text.strip()

        # Извлечение специализаций
        specializations = soup.find_all('li', {'data-qa': 'resume-block-position-specialization'})
        if specializations:
            data['specializations'] = [spec.text.strip() for spec in specializations]

        # Извлечение опыта работы
        experience = soup.find('span', {'data-qa': 'resume-block-title-experience'})
        if experience:
            data['experience'] = experience.text.strip()

        # Извлечение языков
        languages = soup.find_all('p', {'data-qa': 'resume-block-language-item'})
        if languages:
            data['languages'] = [lang.text.strip() for lang in languages]

        # Извлечение гражданства и другой дополнительной информации
        additional_info = soup.find_all('p')
        if additional_info:
            for info in additional_info:
                if "Гражданство:" in info.text:
                    data['citizenship'] = info.text.replace("Гражданство:", "").strip()
                elif "Разрешение на работу:" in info.text:
                    data['work_permit'] = info.text.replace("Разрешение на работу:", "").strip()
                elif "Желательное время в пути до работы:" in info.text:
                    data['travel_time'] = info.text.replace("Желательное время в пути до работы:", "").strip()

        # Извлечение образования
        education_blocks = soup.find_all('div', {'data-qa': 'resume-block-education-item'})
        if education_blocks:
            data['education'] = []
            for block in education_blocks:
                education_data = {}

                # Год окончания
                year = block.find('div', class_='bloko-column_xs-4')
                if year:
                    education_data['year'] = year.text.strip()

                # Название университета и специализация
                university_name = block.find('div', {'data-qa': 'resume-block-education-name'})
                if university_name:
                    education_data['university'] = university_name.text.strip()

                specialization = block.find('div', {'data-qa': 'resume-block-education-organization'})
                if specialization:
                    education_data['specialization'] = specialization.text.strip()

                data['education'].append(education_data)

        return data

    async def get_pages(self, page):
        html_content = await page.content()
        soup = BeautifulSoup(html_content, 'html.parser')

        # Извлечение всех блоков pager-page
        page_blocks = soup.find_all(['a', 'span'], {'data-qa': 'pager-page'})

        print("page_blocks", page_blocks)

        if not len(page_blocks):
            return []

        # Получение последнего блока и извлечение его текста как общее количество страниц
        last_page_num = int(page_blocks[-1].text.strip())

        print("last_page_num", last_page_num)

        # Извлечение href из первого блока
        first_page_href = None
        for block in page_blocks:
            if block.name == 'a' and 'href' in block.attrs:
                first_page_href = block['href']
                base_url = "/".join(page.url.split("/")[:3])
                first_page_href = base_url + first_page_href
                break

        print("first_page_href", first_page_href)

        # Создание списка URL, заменяя page=x на номер страницы
        page_urls = []
        if first_page_href:
            for i in range(0, last_page_num):
                # Заменяем значение page на нужное число
                new_url = re.sub(r'&page=\d+', f'&page={i}', first_page_href)
                page_urls.append(new_url)

        return page_urls

    def recursive_parse(self, element):
        print("RECURSIVE PARSE")
        data = {}

        # Если это заголовок
        title = 'resume-block__title-text' in element.attrs.get('class', [])
        # title = element.has_attr('class') and 'resume-block__title-text' in element['class']
        if title:
            data['title'] = element.text.strip()

        print("PARSE title", title)

        # Если это список
        rows = 'bloko-columns-row' in element.attrs.get('class', [])
        # rows = element.has_attr('class') and 'bloko-columns-row' in element['class']
        if rows:
            data['rows'] = []
            row_data = []
            columns = element.find_all(True, {"class": ['bloko-column', 'bloko-tag']}, recursive=False)
            for col in columns:
                content = ' '.join(col.stripped_strings)
                if content:
                    row_data.append(content)
            data['rows'] = row_data

        print("PARSE rows", rows)

        # Если это просто текст
        if not title and not rows:
            data['text'] = ' '.join(element.stripped_strings)

            print("PARSE text")

            # Рекурсивный обход дочерних блоков
            children = [child for child in element.children]
            if children:
                data['children'] = [self.recursive_parse(child) for child in children]

        return data
