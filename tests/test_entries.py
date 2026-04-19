from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool


@pytest.fixture()
def client() -> Iterator[TestClient]:
    from bus_zeiterfassung import db
    from bus_zeiterfassung.auth import require_login
    from bus_zeiterfassung.main import app
    from bus_zeiterfassung.models import TimeEntry  # noqa: F401  (register table)

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    def _get_session() -> Iterator[Session]:
        with Session(test_engine) as s:
            yield s

    app.dependency_overrides[db.get_session] = _get_session
    app.dependency_overrides[require_login] = lambda: None

    with TestClient(app) as c:
        c.test_engine = test_engine  # type: ignore[attr-defined]
        yield c

    app.dependency_overrides.clear()


def test_start_creates_open_entry(client: TestClient) -> None:
    from bus_zeiterfassung.models import TimeEntry

    resp = client.post("/start")
    assert resp.status_code == 200

    with Session(client.test_engine) as s:  # type: ignore[attr-defined]
        entries = s.exec(select(TimeEntry)).all()
    assert len(entries) == 1
    assert entries[0].start is not None
    assert entries[0].end is None


def test_start_is_idempotent(client: TestClient) -> None:
    from bus_zeiterfassung.models import TimeEntry

    client.post("/start")
    client.post("/start")

    with Session(client.test_engine) as s:  # type: ignore[attr-defined]
        entries = s.exec(select(TimeEntry)).all()
    assert len(entries) == 1


def test_stop_closes_open_entry(client: TestClient) -> None:
    from bus_zeiterfassung.models import TimeEntry

    client.post("/start")
    client.post("/stop")

    with Session(client.test_engine) as s:  # type: ignore[attr-defined]
        entry = s.exec(select(TimeEntry)).one()
    assert entry.end is not None


def test_manual_entry_rejects_end_before_start(client: TestClient) -> None:
    resp = client.post(
        "/entries",
        data={"day": "2026-04-10", "start": "10:00", "end": "09:00"},
    )
    assert resp.status_code == 400


def test_update_and_delete(client: TestClient) -> None:
    from bus_zeiterfassung.models import TimeEntry

    client.post("/entries", data={"day": "2026-04-10", "start": "08:00", "end": "12:00"})
    with Session(client.test_engine) as s:  # type: ignore[attr-defined]
        entry_id = s.exec(select(TimeEntry)).one().id
    assert entry_id is not None

    resp = client.post(
        f"/entries/{entry_id}/update",
        data={"day": "2026-04-10", "start": "09:00", "end": "13:00", "note": "changed"},
    )
    assert resp.status_code == 200

    with Session(client.test_engine) as s:  # type: ignore[attr-defined]
        updated = s.exec(select(TimeEntry)).one()
    assert updated.note == "changed"

    resp = client.post(f"/entries/{entry_id}/delete")
    assert resp.status_code == 200

    with Session(client.test_engine) as s:  # type: ignore[attr-defined]
        assert s.exec(select(TimeEntry)).all() == []
