from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DATA_DIR / "app.db"


class Base(DeclarativeBase):
    pass


def get_engine(db_path: Path = DB_PATH):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}")


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
