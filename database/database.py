from peewee import *
from playhouse.pool import PooledMySQLDatabase
from config import DB_HOST, DB_NAME, DB_SECRET, DB_USER
from datetime import datetime, MINYEAR
from typing import Any, TypeVar

import pymysql

print(DB_HOST, DB_NAME, DB_SECRET, DB_USER)

import MySQLdb

conn = MySQLdb.connect(
      host="rc1a-3r7wr8qzh4gvbrk9.mdb.yandexcloud.net",
      port=3306,
      db="db_digsearch",
      user="user1",
      passwd="testpass",
      ssl={'ca': 'database/MySQL.pem'}
      # ssl={'ca': r'C:\Users\max16\PycharmProjects\dig-search-develop_2\database\MySQL.pem'}
    )

cur = conn.cursor()
cur.execute('SELECT version()')


DB_USER = "user1"
DB_SECRET = "testpass"
DB_NAME = "db_digsearch"
DB_HOST = "rc1a-3r7wr8qzh4gvbrk9.mdb.yandexcloud.net"
DB_PORT = 3306


print(cur.fetchone()[0])

conn.close()

# db = PooledMySQLDatabase(
#     DB_NAME,
#     user=DB_USER,
#     password=DB_SECRET,
#     host=DB_HOST,
#     max_connections=10,  # максимальное количество соединений в пуле
#     stale_timeout=300,  # время в секундах, через которое неиспользуемое соединение будет закрыто
#     ssl = {'ca': 'database/MySQL.pem'}
# )

db = PooledMySQLDatabase(
    DB_NAME,
    user=DB_USER,
    password=DB_SECRET,
    host=DB_HOST,
    max_connections=10,  # максимальное количество соединений в пуле
    stale_timeout=300,  # время в секундах, через которое неиспользуемое соединение будет закрыто
    ssl={'ca': 'database/MySQL.pem'}
    # ssl={'ca': r'C:\Users\max16\PycharmProjects\dig-search-develop_2\database\MySQL.pem'}
)


def zero_date(self):
    return datetime(MINYEAR, 1, 1)


T = TypeVar('T', bound='BaseModel')


class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def _ensure_connection(cls):
        """
        Проверяет соединение и пытается его восстановить при необходимости.
        """
        try:
            cls._meta.database.execute_sql('SELECT 1')
        except InterfaceError:
            cls._meta.database.close()
            cls._meta.database.connect()

    @classmethod
    def select(cls, *fields: Any) -> Select:
        cls._ensure_connection()
        return super().select(*fields)

    @classmethod
    def insert(cls, **data: Any) -> int:
        cls._ensure_connection()
        return super().insert(**data)

    @classmethod
    def update(cls, __data=None, **update: Any) -> int:
        cls._ensure_connection()
        return super().update(__data, **update)

    @classmethod
    def delete(cls) -> int:
        cls._ensure_connection()
        return super().delete()

    @classmethod
    def get(cls, *query: Any) -> T:
        cls._ensure_connection()
        return super().get(*query)


# Company model
class Company(BaseModel):
    name = TextField(unique=True)
    actual_name = TextField()
    city = TextField()
    website = TextField()
    url = TextField()


class SearchTechnology(BaseModel):
    name = TextField(unique=True)


class Resume(BaseModel):
    company = ForeignKeyField(Company, backref='resumes')
    publication_date = DateTimeField(null=True)
    source = TextField(null=True)
    position = TextField(null=True)
    salary = TextField(null=True)
    experience = TextField(null=True)
    citizenship = TextField(null=True)
    work_permit = TextField(null=True)
    travel_time = TextField(null=True)
    specializations = TextField(null=True)  # Storing as a comma-separated string
    languages = TextField(null=True)  # Storing as a comma-separated string
    education = TextField(null=True)  # Storing as a serialized JSON string
    url = TextField(null=True)


class Vacancy(BaseModel):
    company = ForeignKeyField(Company, backref='resumes')
    title = TextField(null=True)
    description = TextField(null=True)
    publication_date = DateTimeField(null=True)
    source = TextField(null=True)  # hh or tadviser
    url = TextField(unique=True)


class Industry(BaseModel):
    name = CharField(unique=True, verbose_name='Название отрасли')


class Passport(BaseModel):
    project_name = TextField()
    integrator = TextField()
    product = TextField()
    technology = TextField()
    updated_date = DateTimeField(null=True)
    company = ForeignKeyField(Company, backref='passports')


class Project(BaseModel):
    client = TextField()
    product = TextField()
    technology = TextField()
    project_description = TextField(null=True)
    updated_date = DateTimeField(null=True)
    company = ForeignKeyField(Company, backref='projects')


class Product(BaseModel):
    count = TextField(null=True)
    href = TextField(null=True)
    name = TextField(null=True)
    technology = TextField(null=True)
    company = ForeignKeyField(Company, backref='products')


# Search list for companies
class SearchCompany(BaseModel):
    company_name = TextField(unique=True)
    active_parsers_count = IntegerField(default=0)
    parser_statuses = TextField(default="{}")


class HHCompanyList(BaseModel):
    name = TextField(unique=True)


class tvcomplist(BaseModel):
    name = TextField(unique=True)


# Create the tables in the database
db.connect()
db.create_tables([Company, SearchCompany, SearchTechnology, Project,
                  Passport, Vacancy, Resume, Industry, Product, HHCompanyList, tvcomplist])

for company in SearchCompany.select():
    company.active_parsers_count = 0
    company.parser_statuses = {}
    company.save()

