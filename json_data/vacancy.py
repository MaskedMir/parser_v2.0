#-*- coding: utf-8 -*-
import json
from datetime import datetime

from database.database import Company, Vacancy, db


# Выполнение запроса с JOIN
# query = (Vacancy
#          .select(Company.name, Vacancy.title, Vacancy.description, Vacancy.source, Vacancy.technology)
#          .join(Company, on=(Vacancy.company_id == Company.id)))
conn = db
cursor = conn.cursor()
query = cursor.execute("SELECT "
                            "company.name, "
                            "vacancy.title, "
                            "vacancy.publication_date, "
                            "vacancy.source, "
                            "vacancy.technology "
                       "FROM "
                            "company "
                       "INNER JOIN "
                            "vacancy "
                       "ON "
                            "company.id = vacancy.company_id")
names = cursor.fetchall()
conn.close()
# Формирование списка словарей
vacancies_list = []
for vacancy in names:
    vacancy_dict = {
        "company_name": vacancy[0],
        "title": vacancy[1],
        "date": vacancy[2],
        "source": vacancy[3],
        "technology": vacancy[4]
    }
    vacancies_list.append(vacancy_dict)

# Преобразование списка в JSON
def custom_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

vacancies_json = json.dumps(vacancies_list, ensure_ascii=False, indent=5, default=custom_converter)


# Печать или сохранение JSON
print(vacancies_json)


