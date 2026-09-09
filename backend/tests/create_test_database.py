"""Create the explicitly named disposable PostgreSQL database used by CI."""

import os
import re

import psycopg
from psycopg import sql

from app.database import DATABASE_URL, DB_NAME


def main() -> None:
    test_database = os.getenv("TEST_DB_NAME", "")
    if not test_database or "test" not in test_database.lower():
        raise RuntimeError("TEST_DB_NAME must be set and contain the word 'test'")
    if test_database == DB_NAME:
        raise RuntimeError("TEST_DB_NAME must differ from DB_NAME")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", test_database):
        raise RuntimeError("TEST_DB_NAME contains unsupported characters")

    connection_url = DATABASE_URL.set(drivername="postgresql", database=DB_NAME)
    with psycopg.connect(connection_url.render_as_string(hide_password=False), autocommit=True) as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (test_database,)
        ).fetchone()
        if exists is None:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(test_database)))
            print(f"Created disposable database {test_database}")
        else:
            print(f"Disposable database {test_database} already exists")


if __name__ == "__main__":
    main()
