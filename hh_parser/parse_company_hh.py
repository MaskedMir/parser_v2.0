from bs4 import BeautifulSoup
import requests
from database import HHCompanyList


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
            'div.bloko-column.bloko-column_container.bloko-column_xs-4.bloko-column_m-8.bloko-column_l-11 table tbody'
        )
        companies = companies_table.find_all('div')
        print(url)
        result = []
        for company in companies:
            name_element = company.select_one('div.bloko-link')
            name = name_element.text.strip() if name_element else company.select_one('a').text.strip()
            # vacancies = company.select_one('td span').text.strip()
            # print("Company:", name)
            result.append(name)
        return result
    except Exception as e:
        print(e)
        return False


"""
разбор ссылки:

https://hh.ru/                                                          домен
employers_list?                                                         категория компании
query=&hhtmFrom=employers_list                                          запрос из категории кампании
&hhtmFromLabel=employer_search_line                                     из линии
&areaId=2                                                               Город/Регион (0-все)
&letter=Г                                                               Фильтр по алфавиту (А-Я)(A-Z)(%23)
&page=2                                                                 Страницы (0-49)
"""


def get_alphabet() -> list:
    """
    Получение списка ссылок на страницы алфавитного заголовка
    Returns: &letter=A-Z-А-Я-%23
    """
    # Генерация списка из всех заглавных букв английского алфавита
    english_uppercase = [chr(i) for i in range(65, 91)]
    # Генерация списка из всех заглавных букв русского алфавита
    russian_uppercase = [chr(i) for i in range(1040, 1072)]
    # Объединение списков
    all_uppercase = english_uppercase + russian_uppercase + ['%23']
    return ['&letter=' + i for i in all_uppercase]


def generate_url():
    """
    Перебор ссылок и передача их в парсер
    Returns:
    """
    base_url = "https://hh.ru/employers_list?query=&hhtmFrom=employers_list&hhtmFromLabel=employer_search_line"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
                                AppleWebKit/537.36 (KHTML, like Gecko)\
                                 Chrome/58.0.3029.110 Safari/537.3'
    }
    k = 0
    letters = get_alphabet()
    for city in range(1, 15001):
        _url = base_url + "&areaId=" + str(city)
        response = requests.get(_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        count_class = soup.find('div', class_='totals--rE1moq2jhLukW5QVcI6L')
        count_span = count_class.find('span', class_='bloko-text_strong')
        _count = count_span.text.strip()
        print(_count)
        if int(_count) > 0:
            if int(_count) > 5000:
                for letter in letters:
                    for page in range(0, 50):
                        result_url = base_url + "&areaId=" + str(city) + letter + "&page=" + str(page)
                        _temp = link_parser(result_url)
                        if _temp:
                            for name in _temp:
                                HHCompanyList.create(name=name)
                            k += 1
                            print(k)
                        else:
                            break

            else:
                for page in range(0, 50):
                    result_url = base_url + "&areaId=" + str(city) + "&page=" + str(page)
                    print(_url)
                    link_parser(result_url)
