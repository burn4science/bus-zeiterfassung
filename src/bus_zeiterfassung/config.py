from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the directory where config.py is, then go up to the project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    pin_hash: str = Field(..., description="argon2 hash of the login PIN")
    secret_key: str = Field(default="", description="session cookie signing key")
    tz: str = "Europe/Berlin"
    template_path: Path = Path(BASE_DIR, "data/Dienstzeitblatt_template.xlsx")
    database_url: str = "sqlite:///data/db.sqlite3"
    export_dir: Path = Path("data/exports")


settings = Settings()  # type: ignore[call-arg]
