# -*- coding: utf-8 -*-
from database.database import db


def search_technology():
    conn = db
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM searchtechnology")
    technologies = cursor.fetchall()
    conn.close()
    return [i[0] for i in technologies]


# Выполнение запроса с JOIN
def company_tv_to_json(query: str = "", date: str = None):
    conn = db
    cursor = conn.cursor()
    cursor.execute("SELECT "
                       "company.name, "
                       "passport.technology, "
                       "passport.updated_date, "
                       "passport.project_name "
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
    technologies = search_technology()
    for company in names:
        company_name = company[0]
        if not technologies:
            pass
        elif any(tech.lower() in company[1].lower() for tech in technologies):
            pass
        else:
            continue
        if query.lower() == company_name.lower() or query == "":
            if company_name not in companies_dict:
                companies_dict[company_name] = {
                    "passport": []
                }
            passport_dict = {
                "technology": company[1],
                "date": company[2].isoformat() if company[2] is not None else None,
                "source": "TV",
                "url": company[3]
            }
            if date is None:
                companies_dict[company_name]["passport"].append(passport_dict)
            elif date == passport_dict["date"]:
                companies_dict[company_name]["passport"].append(passport_dict)
    return companies_dict


if __name__ == '__main__':
    print(company_tv_to_json())
