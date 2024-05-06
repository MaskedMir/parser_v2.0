from bs4 import BeautifulSoup

html_code = """
ваш HTML-код здесь
"""

# Создаем объект BeautifulSoup
soup = BeautifulSoup(html_code, 'html.parser')

# Открываем файл для записи ссылок
with open('links.txt', 'w') as file:
    # Ищем все теги 'a' с атрибутом 'href'
    for link in soup.find_all('a', href=True):
        # Получаем значение атрибута 'href' (ссылку)
        href = link['href']
        # Записываем ссылку в файл
        file.write(href + '\n')

print("Ссылки были успешно записаны в файл 'links.txt'")
