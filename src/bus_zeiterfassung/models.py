from datetime import date, datetime, time

from sqlmodel import Field, SQLModel


class TimeEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    day: date = Field(index=True)
    start: time | None = None
    end: time | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
