import asyncio
from time import time
from bs4 import BeautifulSoup
import requests
import logging

from postgresql_db.query import insert_industries_tv

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(asctime)s %(message)s")
HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
                            AppleWebKit/537.36 (KHTML, like Gecko)\
                             Chrome/58.0.3029.110 Safari/537.3'
        }
base_url = "https://www.tadviser.ru/index.php/Компании?cache=no"
response = ""


def parser():
    global response
    try:
        start = time()
        response = requests.get(base_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')

        tables = soup.find_all('table', id='thechPageTableNoIT')
        if len(tables) >= 2:
            second_table = tables[1]
            industries = second_table.find_all('td')
            for i, e in enumerate(industries):
                href = e.select_one('a')['href']
                if not ('no&city' in href):
                    try:
                        name = e.select_one('a').text.strip()
                        div_with_count = industries[i+1].find('div', style='text-align: right;')
                        _count = div_with_count.select_one('a').text.strip()
                        count = int(''.join(filter(str.isdigit, _count)))
                        # with open('file.txt', 'a', encoding='utf-8') as f:
                        #     f.write(f'{name} {count}\n')

                        insert_industries_tv(name, count)
                    except Exception:
                        continue
                else:
                    continue
        else:
            print("Вторая таблица не найдена")

            # asyncio.run(async_insert_industries_tv(name, count))
        end = time()
        logging.info(f'статус {response.status_code} | {round(end - start)} sec')
    except Exception as e:
        logging.error(f'ОШИБКА ЧТЕНИЯ СТРАНИЦЫ | {e}')
        logging.error(f'статус {response.status_code} | {base_url}')
        return False


if __name__ == '__main__':
    parser()
