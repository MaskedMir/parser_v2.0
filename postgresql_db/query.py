# import asyncio
import logging
# from sqlalchemy import text, insert
from postgresql_db.database import async_session_factory
from postgresql_db.model import CompanyHH

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(asctime)s %(message)s")


# insert для записи имен компаний
async def async_insert_company_hh(data):
    async with async_session_factory() as session:
        try:
            session.add(CompanyHH(name=data))
            await session.commit()
        except Exception as e:
            logging.info(e.args[0])


if __name__ == '__main__':
    pass
    # create_tables()
    # insert_data()
    # asyncio.run(async_insert_data('bobra'))
