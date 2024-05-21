import asyncio
import aiohttp
from bs4 import BeautifulSoup
from time import time
import logging

from database.database import HHCompList

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(asctime)s %(message)s")
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
                    AppleWebKit/537.36 (KHTML, like Gecko)\
                     Chrome/58.0.3029.110 Safari/537.3'
}

with open('regions.txt', 'r') as file:                  # номера регионов
    REGIONS = [line.strip() for line in file]


async def parser(url: str) -> list or bool:
    """
    Парсинг страницы с компаниями, функция вытаскивает названия компаний

    Args: url (str)

    Returns: list[name] or bool(False)
    :param url: str
    :return: company name: list
    :exception 404: False
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                companies_table = soup.select_one(              # необходимый блок с названиями компаний
                    'div.bloko-column.bloko-column_container.bloko-column_xs-4.bloko-column_m-8.bloko-column_l-11 \
                    table tbody'
                )
                companies = companies_table.find_all('div')
                logging.info(f'статус: {response.status} | {url}')
                result = []
                for company in companies:
                    name_element = company.select_one('div.bloko-link')
                    name = name_element.text.strip() if name_element else company.select_one('a').text.strip()
                    result.append(name)
                return result
    except Exception as e:
        logging.error(f'ОШИБКА ЧТЕНИЯ СТРАНИЦЫ | {e}')
        logging.error(f'{url}')
        return False


async def process_page(semaphore, region, letter, page, base_url) -> None or bool:
    """
    Функция вызывает parser(), вытаскивает названия компаний и записывает их в БД

    Args: semaphore, region (str), letter (str), page (int), base_url (str)

    :param semaphore:
    :param region:
    :param letter:
    :param page:
    :param base_url:
    :return: None or bool(False)
    """
    async with semaphore:
        start_time = time()
        result_url = base_url + f"&areaId={region}&letter={letter}&page={page}"
        _temp = await parser(result_url)
        end_time = time()
        if _temp:
            _start = time()
            for name in _temp:
                if not HHCompList.select().where(HHCompList.name == name).exists():
                    HHCompList.create(name=name)
            _end = time()
            logging.info(f'добавлено: {len(_temp)} : {_end - _start} sec')
            logging.info(f'{region=} {letter=} {page=} | {round(end_time - start_time, 3)} sec')
        else:
            return False


async def paginator(base_url, session, letters, semaphore) -> None:
    """
    Функция вызывает process_page(), создает ссылки и формирует задачи для parser

    Args: base_url (str), session (aiohttp.ClientSession), letters (list), semaphore (asyncio.Semaphore)

    Returns: None

    :param base_url:
    :param session:
    :param letters:
    :param semaphore:
    :return:
    """
    for region in REGIONS:
        async with session.get(base_url + f"&areaId={region}", headers=HEADERS) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            count_class = soup.find('div', class_='totals--rE1moq2jhLukW5QVcI6L')
            count_span = count_class.find('span', class_='bloko-text_strong')
            count = int(count_span.text.strip())
            logging.info(f'{count} компаний в регионе')

        if count > 0:
            if count > 5000:
                for letter in letters:
                    tasks = [process_page(semaphore, region, letter, page, base_url)
                             for page in range(int(count/100)+1)]
                    await asyncio.gather(*tasks)
            else:
                tasks = [process_page(semaphore, region, "", page, base_url)
                         for page in range(int(count/100)+1)]
                await asyncio.gather(*tasks)


def get_alphabet() -> list:
    """
    Функция формирует часть запроса для перехода по буквам алфавита и ссылке на числа %23

    Args: None

    Returns: list[str]
    """
    english_uppercase = [chr(i) for i in range(65, 91)]
    russian_uppercase = [chr(i) for i in range(1040, 1072)]
    all_uppercase = english_uppercase + russian_uppercase + ['%23']
    return ['&letter=' + i for i in all_uppercase]


async def main():
    base_url = "https://hh.ru/employers_list?query=&hhtmFrom=employers_list&hhtmFromLabel=employer_search_line"
    letters = get_alphabet()          # Формируем список букв алфавита и ссылки на числа
    semaphore = asyncio.Semaphore(2)  # Устанавливаем максимальное количество одновременных запросов
    async with aiohttp.ClientSession() as session:
        await paginator(base_url, session, letters, semaphore)

# if __name__ == '__main__':
#     asyncio.run(main())
