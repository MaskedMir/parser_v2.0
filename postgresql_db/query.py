# import asyncio
import logging
# from sqlalchemy import text, insert
from postgresql_db.database import async_session_factory, session_factory
from postgresql_db.model import CompanyHH, CompanyTV, IndustriesTV

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(asctime)s %(message)s")


# insert для записи имен компаний hh.ru
async def async_insert_company_hh(name):
    async with async_session_factory() as session:
        try:
            session.add(CompanyHH(name=name))
            await session.commit()
        except Exception as e:
            logging.info(e.args[0])


# insert для записи имен компаний tadviser.ru
async def async_insert_company_tv(name):
    async with async_session_factory() as session:
        try:
            session.add(CompanyTV(name=name))
            await session.commit()
        except Exception as e:
            logging.info(e.args[0])


# insert для записи отраслей tadviser.ru
def insert_industries_tv(name, count):
    with session_factory() as session:
        try:
            session.add(IndustriesTV(name=name, count=count))
            session.commit()
        except Exception as e:
            logging.info(e.args[0])


if __name__ == '__main__':
    pass
    # create_tables()
    # insert_data()
    # asyncio.run(async_insert_data('bobra'))
