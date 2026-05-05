from fastapi.testclient import TestClient
from sqlmodel import Session, select


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
        data={"day": "2026-04-10", "start": "09:00", "end": "13:00"},
    )
    assert resp.status_code == 200

    with Session(client.test_engine) as s:  # type: ignore[attr-defined]
        updated = s.exec(select(TimeEntry)).one()
    assert updated.start is not None

    resp = client.post(f"/entries/{entry_id}/delete")
    assert resp.status_code == 200

    with Session(client.test_engine) as s:  # type: ignore[attr-defined]
        assert s.exec(select(TimeEntry)).all() == []
