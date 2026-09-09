import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from collections.abc import Generator
from sqlalchemy.orm import Session

load_dotenv()


raw_database_url = os.getenv("DATABASE_URL", "").strip()

if raw_database_url:
    DATABASE_URL = make_url(raw_database_url)
    if DATABASE_URL.drivername in {"postgres", "postgresql"}:
        DATABASE_URL = DATABASE_URL.set(drivername="postgresql+psycopg")
    if not DATABASE_URL.drivername.startswith("postgresql"):
        raise RuntimeError("DATABASE_URL must use PostgreSQL")
    DB_HOST = DATABASE_URL.host
    DB_PORT = str(DATABASE_URL.port or 5432)
    DB_NAME = DATABASE_URL.database
    DB_USER = DATABASE_URL.username
    DB_PASSWORD = DATABASE_URL.password
else:
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        raise RuntimeError(
            "Set DATABASE_URL or all of DB_HOST, DB_NAME, DB_USER and DB_PASSWORD"
        )

    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
    )


def _environment_flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


engine = create_engine(
    DATABASE_URL,
    echo=_environment_flag("SQL_ECHO"),
    pool_pre_ping=True,
    pool_recycle=300,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
