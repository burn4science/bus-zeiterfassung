from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from bus_zeiterfassung.config import settings
from bus_zeiterfassung.store import TimeEntryStore

_db_path = settings.database_url.removeprefix("sqlite:///")
Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def get_store(session: Annotated[Session, Depends(get_session)]) -> TimeEntryStore:
    return TimeEntryStore(session)
