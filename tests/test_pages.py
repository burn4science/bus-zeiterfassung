from fastapi.testclient import TestClient


def test_today_page(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200


def test_today_page_with_date(client: TestClient) -> None:
    resp = client.get("/?d=2026-04-10")
    assert resp.status_code == 200


def test_month_page(client: TestClient) -> None:
    resp = client.get("/month")
    assert resp.status_code == 200


def test_month_page_with_key(client: TestClient) -> None:
    resp = client.get("/month?m=2026-04")
    assert resp.status_code == 200


def test_month_page_invalid_key(client: TestClient) -> None:
    resp = client.get("/month?m=invalid")
    assert resp.status_code == 400


def test_login_page(client: TestClient) -> None:
    resp = client.get("/login")
    assert resp.status_code == 200


def test_login_wrong_pin(client: TestClient) -> None:
    resp = client.post("/login", data={"pin": "000000"}, follow_redirects=False)
    assert resp.status_code == 401
