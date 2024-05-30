# -*- coding: utf-8 -*-
from database.database import db


# Выполнение запроса с JOIN
def company_tv_to_json(query: str, date: str = None):
    conn = db
    cursor = conn.cursor()
    cursor.execute("SELECT "
                       "company.name, "
                       "passport.product, "
                       "passport.updated_date, "
                       "passport.technology "
                   "FROM "
                       "company "
                   "INNER JOIN "
                       "passport "
                   "ON "
                       "company.id = passport.company_id")
    names = cursor.fetchall()
    conn.close()
    # Формирование списка словарей
    companies_dict = {}
    for company in names:
        company_name = company[0]
        if query.lower() == company_name.lower() or query == "":
            if company_name not in companies_dict:
                companies_dict[company_name] = {
                    "passport": []
                }
            passport_dict = {
                "product": company[1],
                "date": company[2].isoformat() if company[2] is not None else None,
                "source": "TV; проекты",
                "technology": company[3]
            }
            if date == passport_dict["date"]:
                companies_dict[company_name]["passport"].append(passport_dict)
            elif date is None:
                companies_dict[company_name]["passport"].append(passport_dict)
    return companies_dict
