# -*- coding: utf-8 -*-

import pandas as pd
from database.database import hhindustry, hhsubindustry

df_industry = pd.read_csv('industry.csv', sep=';', encoding='cp1251')
df_sub_industry = pd.read_csv('sub_industry.csv', sep=';', encoding='cp1251')


def create_industry_table():
    # df_industry.to_sql('hhindustry', con=cur, if_exists='replace', index=False)
    for index, row in df_industry.iterrows():
        hhindustry.create(id_industry=row['id_industry'], name_industry=row['name_industry'])
        # print(row['name_industry'])

def create_sub_industry_table():
    # df_sub_industry.to_sql('hhsubindustry', con=cur, if_exists='replace', index=False)
    for index, row in df_sub_industry.iterrows():
        hhsubindustry.create(id_industry=row['id_industry'], id_sub_industry=row['id_sub_industry'], name_sub_industry=row['name_sub_industry'])
        # print(row['id_sub_industry'])

# if __name__ == '__main__':
#     pass
#     # print(df_sub_industry['id_sub_industry'])
#     # print(df_industry)
#     # create_industry_table()
    # create_sub_industry_table()
