from bs4 import BeautifulSoup
import requests
from database import tvcomplist


def link_parser(url):
    try:
        # url = "https://hh.ru/employers_list?page=2" #
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
                            AppleWebKit/537.36 (KHTML, like Gecko)\
                             Chrome/58.0.3029.110 Safari/537.3'
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        companies_table = soup.select_one(
            'table.sortable.cwiki_table'
        )

        companies = companies_table.find_all('td')
        print(url)
        result = []
        for company in companies:
            href = company.select_one('a')['href']
            if not ('no&city' in href):
                name_element = company.select_one('a')
                name = name_element.text.strip() if name_element else company.select_one('a').text.strip()
                result.append(name)

            # vacancies = company.select_one('td span').text.strip()
            # print("Company:", name)
        return result
    except Exception as e:
        print(e)
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
    # Генерация списка из всех заглавных букв английского алфавита A-Z
    english_uppercase = [chr(i) for i in range(65, 91)]
    # Генерация списка из всех заглавных букв русского алфавита А-Я+Ё
    russian_uppercase = [chr(i) for i in range(1040, 1072)]
    russian_uppercase.append('Ё')
    # Генерация списка из всех цифр 1 - 8
    numbers = [str(i) for i in range(1, 9)]
    # Объединение списков
    all_uppercase = numbers + english_uppercase + russian_uppercase
    return ['&letter=' + i for i in all_uppercase]


def generate_url():
    """
    Перебор ссылок и передача их в парсер
    Returns:
    """
    base_url = "https://www.tadviser.ru/index.php/Компании?cache=no"
    k = 0
    i = 0
    letters = get_alphabet()
    for letter in letters:
        result_url = base_url + letter
        _temp = link_parser(result_url)
        if _temp:
            for name in _temp:
                # HHCompanyList.create(name=name)
                # Подключение к БД
                tvcomplist.create(name=name)
                i += 1
                print(f'{i}: {name}')
                pass
            k += 1
            print(k)
        else:
            continue


if __name__ == '__main__':
    generate_url()
