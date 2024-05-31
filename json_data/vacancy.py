# -*- coding: utf-8 -*-
from database.database import db


# Выполнение запроса с JOIN
def vacancy_to_json(query: str = "", date: str = None):
    conn = db
    cursor = conn.cursor()
    cursor.execute("SELECT "
                       "company.name, "
                       "vacancy.title, "
                       "vacancy.publication_date, "
                       "vacancy.technology, "
                       "vacancy.url "
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
        if query.lower() == company_name.lower() or query == "":
            if company_name not in companies_dict:
                companies_dict[company_name] = {
                    "vacancies": []
                }
            vacancy_dict = {
                "title": vacancy[1],
                "date": vacancy[2].isoformat() if vacancy[2] is not None else None,
                "source": "HH",
                "technology": vacancy[3],
                "url": vacancy[4]
            }
            if date == vacancy_dict["date"]:
                companies_dict[company_name]["vacancies"].append(vacancy_dict)
            elif date is None:
                companies_dict[company_name]["vacancies"].append(vacancy_dict)
    return companies_dict
