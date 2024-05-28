# -*- coding: utf-8 -*-
from database.database import db


# Выполнение запроса с JOIN
def company_tv_to_json():
    conn = db
    cursor = conn.cursor()
    cursor.execute("SELECT "
                       "company.name, "
                       "passport.integrator, "
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
        if company_name not in companies_dict:
            companies_dict[company_name] = {
                "passport": []
            }
        passport_dict = {
            "integrator": company[1],
            "product": company[2],
            "date": company[3].isoformat() if company[3] is not None else None,
            "source": "TV",
            "technology": company[4]
        }
        companies_dict[company_name]["passport"].append(passport_dict)
    return companies_dict
