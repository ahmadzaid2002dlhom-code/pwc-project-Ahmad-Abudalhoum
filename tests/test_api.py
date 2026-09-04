from collections.abc import Generator
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import service
from app.database import Base, get_db
from app.extraction import LLMResponseError, LLMUnavailableError
from app.main import app
from app.schemas import LLMExtractionCandidate


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(engine, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        with test_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_candidate(**overrides: object) -> LLMExtractionCandidate:
    data = {
        "lessor": "Apex Holdings LLC",
        "lessee": "Vertex Tech Solutions Corp",
        "commencement_date": date(2024, 6, 1),
        "expiration_date": date(2026, 5, 31),
        "monthly_rent": Decimal("12500.00"),
        "currency": "aed",
        "termination_notice_period_days": 90,
    }
    data.update(overrides)
    return LLMExtractionCandidate.model_validate(data)


def mock_extraction(
    monkeypatch: pytest.MonkeyPatch,
    result: LLMExtractionCandidate | Exception,
) -> Mock:
    extractor = Mock()
    if isinstance(result, Exception):
        extractor.side_effect = result
    else:
        extractor.return_value = result
    monkeypatch.setattr(service, "extract_contract", extractor)
    return extractor


def test_post_extract_returns_created_contract(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extractor = mock_extraction(monkeypatch, make_candidate())

    response = client.post("/api/v1/extract", json={"text": "Commercial lease"})

    assert response.status_code == 201
    assert response.json() == {
        "lessor": "Apex Holdings LLC",
        "lessee": "Vertex Tech Solutions Corp",
        "commencement_date": "2024-06-01",
        "expiration_date": "2026-05-31",
        "monthly_rent": "12500.00",
        "currency": "AED",
        "termination_notice_period_days": 90,
        "contract_duration_days": 729,
        "id": 1,
    }
    extractor.assert_called_once_with("Commercial lease")


@pytest.mark.parametrize(
    ("overrides", "expected_message"),
    [
        (
            {"expiration_date": date(2024, 5, 31)},
            "expiration_date must not be before commencement_date",
        ),
        ({"monthly_rent": Decimal("-1.00")}, "greater than or equal to 0"),
        ({"lessor": None}, "valid string"),
    ],
)
def test_post_extract_rejects_invalid_contract_without_storage(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, object],
    expected_message: str,
) -> None:
    mock_extraction(monkeypatch, make_candidate(**overrides))

    response = client.post("/api/v1/extract", json={"text": "Invalid lease"})

    assert response.status_code == 422
    assert expected_message in str(response.json()["detail"])
    assert client.get("/api/v1/contracts").json() == []


def test_get_contracts_lists_stored_contracts(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extractor = mock_extraction(monkeypatch, make_candidate())
    client.post("/api/v1/extract", json={"text": "First lease"})
    extractor.return_value = make_candidate(lessor="Second Lessor")
    client.post("/api/v1/extract", json={"text": "Second lease"})

    response = client.get("/api/v1/contracts")

    assert response.status_code == 200
    assert [contract["lessor"] for contract in response.json()] == [
        "Apex Holdings LLC",
        "Second Lessor",
    ]


def test_get_contract_by_id(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_extraction(monkeypatch, make_candidate())
    created = client.post("/api/v1/extract", json={"text": "Commercial lease"}).json()

    response = client.get(f"/api/v1/contracts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_contract_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/contracts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Contract not found"}


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (LLMUnavailableError("timed out"), 503),
        (LLMResponseError("unusable"), 502),
    ],
)
def test_post_extract_maps_llm_failures(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected_status: int,
) -> None:
    mock_extraction(monkeypatch, error)

    response = client.post("/api/v1/extract", json={"text": "Commercial lease"})

    assert response.status_code == expected_status
    assert client.get("/api/v1/contracts").json() == []


def test_post_extract_hides_unexpected_failures(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_extraction(monkeypatch, RuntimeError("internal detail"))

    response = client.post("/api/v1/extract", json={"text": "Commercial lease"})

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
