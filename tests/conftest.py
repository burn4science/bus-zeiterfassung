import os
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.setdefault("PIN_HASH", "$argon2id$v=19$m=65536,t=3,p=4$salt1234567890ab$" + "a" * 43)
os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-please-ok")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture()
def tmp_export_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    from bus_zeiterfassung import config

    monkeypatch.setattr(config.settings, "export_dir", tmp_path)
    yield tmp_path
