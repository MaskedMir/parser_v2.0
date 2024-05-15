# from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.orm import Mapped, mapped_column
from postgresql_db.database import Base
from postgresql_db.database import sync_engine


class CompanyHH(Base):
    __tablename__ = 'company_hh'
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)


Base.metadata.create_all(sync_engine)
