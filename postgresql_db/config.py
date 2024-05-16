from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @property
    def DATABASE_URL_psycopg2(self) -> object:
        # postgres+psycopg2://postgres:postgres@localhost:5432/name
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DATABASE_URL_asyncpg(self) -> object:
        # postgres+psycopg2://postgres:postgres@localhost:5432/name
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file="postgresql.env")


settings = Settings(
    DB_HOST="localhost",
    DB_PORT=5432,
    DB_USER="postgres",
    DB_PASS="1234",
    DB_NAME="localparser"
)
