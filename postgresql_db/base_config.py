from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import MetaData
from sqlalchemy import func, select
from sqlalchemy.orm import column_property
from sqlalchemy import DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

POSTGRES_USERNAME = 'user1'
POSTGRES_PASSWORD = 'testpass'
POSTGRES_DBNAME = 'hr_parser_db'
POSTGRES_HOST = 'rc1a-lelb808lx7mwmty0.mdb.yandexcloud.net' 
POSTGRES_PORT = '6432'  

DATABASE_URI = f'postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DBNAME}'
engine = create_engine(DATABASE_URI, echo=False)

Session = sessionmaker(bind=engine)
session = Session()