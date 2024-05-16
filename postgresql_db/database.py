import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy import URL, create_engine, text
from postgresql_db.config import settings

sync_engine = create_engine(
    url=settings.DATABASE_URL_psycopg2,
    echo=False,
)

async_engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=False,
)


session_factory = sessionmaker(sync_engine)
async_session_factory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass
