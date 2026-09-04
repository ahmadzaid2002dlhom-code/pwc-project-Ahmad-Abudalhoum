from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base, create_contract, get_contract, list_contracts
from app.schemas import LLMExtractionCandidate, ValidatedContract


@pytest.fixture
def db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def make_contract(lessor: str = "Apex Holdings LLC") -> ValidatedContract:
    return ValidatedContract(
        lessor=lessor,
        lessee="Vertex Tech Solutions Corp",
        commencement_date=date(2024, 6, 1),
        expiration_date=date(2026, 5, 31),
        monthly_rent=Decimal("12500.00"),
        currency="AED",
        termination_notice_period_days=90,
    )


def test_create_and_get_contract(db: Session) -> None:
    created = create_contract(db, make_contract())
    created_id = created.id
    db.expunge_all()

    stored = get_contract(db, created_id)
    assert stored is not None
    assert stored.lessor == "Apex Holdings LLC"
    assert stored.monthly_rent == Decimal("12500.00")
    assert get_contract(db, created_id + 1) is None


def test_list_contracts(db: Session) -> None:
    first = create_contract(db, make_contract("First Lessor"))
    second = create_contract(db, make_contract("Second Lessor"))

    assert [record.id for record in list_contracts(db)] == [first.id, second.id]


def test_extraction_candidate_is_not_persisted(db: Session) -> None:
    invalid_candidate = LLMExtractionCandidate(
        lessor="Apex Holdings LLC",
        lessee="Vertex Tech Solutions Corp",
        commencement_date=date(2026, 5, 31),
        expiration_date=date(2024, 6, 1),
        monthly_rent=Decimal("-1.00"),
        currency="AED",
        termination_notice_period_days=90,
    )

    with pytest.raises(TypeError, match="ValidatedContract"):
        create_contract(db, invalid_candidate)  # type: ignore[arg-type]

    assert list_contracts(db) == []
