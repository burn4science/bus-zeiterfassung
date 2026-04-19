from pathlib import Path

from fastapi.templating import Jinja2Templates

_WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def _weekday_de(d) -> str:
    return _WEEKDAYS_DE[d.weekday()]


templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.filters["weekday_de"] = _weekday_de
