import asyncio
import logging
import aiohttp

from time import time
from bs4 import BeautifulSoup
# from postgresql_db.query import async_insert_company_tv
from database.database import tvcomplist
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(asctime)s %(message)s")
HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
                            AppleWebKit/537.36 (KHTML, like Gecko)\
                             Chrome/58.0.3029.110 Safari/537.3'
        }


async def link_parser(url):
    """
    Парсер страницы с названиями компаний
    :param url: str
    :return: company name: list
    :exception 404: False
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                # response = requests.get(url, headers=HEADERS)
        companies_table = soup.select_one(
            'table.sortable.cwiki_table'
        )

        companies = companies_table.find_all('td')
        logging.info(f'статус: {response.status} | {url}')
        result = []
        for company in companies:
            href = company.select_one('a')['href']
            if not ('no&city' in href):
                name_element = company.select_one('a')
                name = name_element.text.strip() if name_element else company.select_one('a').text.strip()
                result.append(name)
        return result
    except Exception as e:
        logging.error(f'ОШИБКА ЧТЕНИЯ СТРАНИЦЫ | {e}')
        logging.error(f'{url}')
        return False


"""
разбор ссылки:

https://www.tadviser.ru/index.php/Компании?cache=no         Постоянная ссылка
&letter=Ш                                                   Переход
"""


def get_alphabet() -> list:
    """
    Получение списка ссылок на страницы алфавитного заголовка
    Returns: &letter=A-Z-А-Я-0-9
    """
    english_uppercase = [chr(i) for i in range(65, 91)]
    russian_uppercase = [chr(i) for i in range(1040, 1072)]
    russian_uppercase.append('Ё')
    numbers = [str(i) for i in range(1, 9)]
    all_uppercase = numbers + english_uppercase + russian_uppercase
    return ['&letter=' + i for i in all_uppercase]


async def generate_url(base_url, letters, semaphore):
    """
    Перебор ссылок и передача их в парсер
    Returns:
    """
    async with semaphore:
        for letter in letters:
            start = time()
            result_url = base_url + letter
            end = time()
            _temp = await link_parser(result_url)
            if _temp:
                _start = time()
                for name in _temp:
                    if not tvcomplist.select().where(tvcomplist.name == name).exists():
                        tvcomplist.create(name=name)
                _end = time()
                logging.info(f'добавлено: {len(_temp)} : {_end - _start} sec')
                logging.info(f'{letter=} | {round(end - start)} sec')



async def main():
    base_url = "https://www.tadviser.ru/index.php/Компании?cache=no"
    letters = get_alphabet()
    semaphore = asyncio.Semaphore(2)
    await generate_url(base_url, letters, semaphore)

# if __name__ == '__main__':
#     asyncio.run(main())
