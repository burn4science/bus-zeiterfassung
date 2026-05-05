import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

os.environ.setdefault("PIN_HASH", "$argon2id$v=19$m=65536,t=3,p=4$salt1234567890ab$" + "a" * 43)
os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-please-ok")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


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


@pytest.fixture()
def tmp_export_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    from bus_zeiterfassung import config

    monkeypatch.setattr(config.settings, "export_dir", tmp_path)
    yield tmp_path
