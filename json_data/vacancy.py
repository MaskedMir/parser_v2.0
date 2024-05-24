# -*- coding: utf-8 -*-
import json
from datetime import datetime
from database.database import db

# Выполнение запроса с JOIN
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
companies_dict = {}
for vacancy in names:
    company_name = vacancy[0]
    if company_name not in companies_dict:
        companies_dict[company_name] = {
            "company_name": company_name,
            "vacancies": []
        }
    vacancy_dict = {
        "title": vacancy[1],
        "date": vacancy[2],
        "source": vacancy[3],
        "technology": vacancy[4]
    }
    companies_dict[company_name]["vacancies"].append(vacancy_dict)
vacancies_list = list(companies_dict.values())


# Преобразование списка в JSON
def custom_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


vacancies_json = json.dumps(vacancies_list, ensure_ascii=False, indent=5, default=custom_converter)

# print(vacancies_json)
