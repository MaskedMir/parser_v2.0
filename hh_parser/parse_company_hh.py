from bs4 import BeautifulSoup
import requests

url = "https://hh.ru/employers_list?page=2"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

companies_table = soup.select_one('div.bloko-column.bloko-column_container.bloko-column_xs-4.bloko-column_m-8.bloko-column_l-11 table tbody')
companies = companies_table.find_all('div')
# print(companies)


k = 0
for company in companies:
    k += 1
    name_element = company.select_one('div.bloko-link')
    name = name_element.text.strip() if name_element else company.select_one('a').text.strip()
    vacancies = company.select_one('td span').text.strip()
    print("Company:", name)
    print("Vacancies:", vacancies)
    print("-" * 50, k)