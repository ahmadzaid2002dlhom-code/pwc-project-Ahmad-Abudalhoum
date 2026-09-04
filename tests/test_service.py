from collections.abc import Generator
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base, list_contracts
from app.schemas import LLMExtractionCandidate
from app.service import ContractService


@pytest.fixture
def db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


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


def test_process_contract_validates_calculates_and_persists(db: Session) -> None:
    candidate = make_candidate()
    extractor = Mock(return_value=candidate)
    service = ContractService(db, extractor=extractor)

    contract = service.process_contract("Commercial lease text")

    extractor.assert_called_once_with("Commercial lease text")
    assert contract.currency == "AED"
    assert contract.contract_duration_days == 729

    stored = list_contracts(db)
    assert len(stored) == 1
    assert stored[0].lessor == "Apex Holdings LLC"
    assert stored[0].currency == "AED"


def test_process_contract_does_not_persist_invalid_candidate(db: Session) -> None:
    candidate = make_candidate(
        expiration_date=date(2024, 5, 31),
        monthly_rent=Decimal("-1.00"),
    )
    extractor = Mock(return_value=candidate)
    service = ContractService(db, extractor=extractor)

    with pytest.raises(ValidationError):
        service.process_contract("Invalid commercial lease text")

    extractor.assert_called_once_with("Invalid commercial lease text")
    assert list_contracts(db) == []
