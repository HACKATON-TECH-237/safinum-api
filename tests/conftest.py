from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

FIXTURES = Path(__file__).parent / "fixtures"


def make_client(**overrides) -> TestClient:
    settings = Settings(_env_file=None, glossary_dir=FIXTURES / "glossary", **overrides)
    return TestClient(create_app(settings))


@pytest.fixture
def client():
    with make_client() as c:
        yield c


def translate(client: TestClient, *items: dict, target: str = "tst") -> list[dict]:
    resp = client.post("/api/v1/translate", json={"target_lang": target, "items": list(items)})
    assert resp.status_code == 200, resp.text
    return resp.json()["items"]
