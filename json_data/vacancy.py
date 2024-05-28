# -*- coding: utf-8 -*-
from database.database import db


# Выполнение запроса с JOIN
def vacancy_to_json():
    conn = db
    cursor = conn.cursor()
    cursor.execute("SELECT "
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
            "date": vacancy[2].isoformat() if vacancy[2] is not None else None,
            "source": vacancy[3],
            "technology": vacancy[4]
        }
        companies_dict[company_name]["vacancies"].append(vacancy_dict)
    return companies_dict
