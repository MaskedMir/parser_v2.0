from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Float, select, update, delete
from sqlalchemy.orm import relationship, sessionmaker
POSTGRES_USERNAME = 'user1'
POSTGRES_PASSWORD = 'testpass'
POSTGRES_DBNAME = 'hr_parser_db'
POSTGRES_HOST = 'rc1a-lelb808lx7mwmty0.mdb.yandexcloud.net'
POSTGRES_PORT = '6432'

DATABASE_URI = f'postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DBNAME}'
DATABASE_URI_a = f'postgresql+asyncpg://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DBNAME}'
engine = create_engine(DATABASE_URI, echo=False)

Session = sessionmaker(bind=engine)
session = Session()



sync_engine = create_engine(
    url=DATABASE_URI,
    echo=False,
)

async_engine = create_async_engine(
    url=DATABASE_URI_a,
    echo=False,
)


session_factory = sessionmaker(sync_engine)
async_session_factory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class CRUDMixin:
    @classmethod
    async def get(cls, session: AsyncSession, id: int):
        query = select(cls).filter_by(id=id)
        result = await session.execute(query)
        return result.scalars().first()

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs):
        instance = cls(**kwargs)
        session.add(instance)
        await session.commit()
        await session.refresh(instance)
        return instance

    @classmethod
    async def update(cls, session: AsyncSession, id: int, **kwargs):
        query = update(cls).where(cls.id == id).values(**kwargs).execution_options(synchronize_session="fetch")
        await session.execute(query)
        await session.commit()
        return await cls.get(session, id)

    @classmethod
    async def delete(cls, session: AsyncSession, id: int):
        query = delete(cls).where(cls.id == id).execution_options(synchronize_session="fetch")
        await session.execute(query)
        await session.commit()



class Base(DeclarativeBase, CRUDMixin):
    pass
