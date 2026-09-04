from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas import ValidatedContract


def make_contract(**overrides: object) -> ValidatedContract:
    data = {
        "lessor": "Northwind Properties",
        "lessee": "Contoso Ltd",
        "commencement_date": date(2025, 1, 1),
        "expiration_date": date(2025, 12, 31),
        "monthly_rent": Decimal("1250.00"),
        "currency": "USD",
        "termination_notice_period_days": 30,
    }
    data.update(overrides)
    return ValidatedContract.model_validate(data)


def test_valid_contract() -> None:
    contract = make_contract()

    assert contract.lessor == "Northwind Properties"
    assert contract.monthly_rent == Decimal("1250.00")


def test_negative_monthly_rent_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_contract(monthly_rent=Decimal("-0.01"))


def test_expiration_before_commencement_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_contract(expiration_date=date(2024, 12, 31))


def test_currency_is_normalized_and_validated() -> None:
    assert make_contract(currency=" eur ").currency == "EUR"

    for invalid_currency in ("US", "US1", "EURO"):
        with pytest.raises(ValidationError):
            make_contract(currency=invalid_currency)


def test_contract_duration_is_calculated_from_dates() -> None:
    contract = make_contract(
        commencement_date=date(2024, 1, 1),
        expiration_date=date(2024, 2, 1),
    )

    assert contract.contract_duration_days == 31
