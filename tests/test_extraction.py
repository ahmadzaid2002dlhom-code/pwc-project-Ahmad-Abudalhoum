from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app import extraction
from app.schemas import LLMExtractionCandidate


def test_extract_contract_uses_one_structured_request(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = LLMExtractionCandidate(
        lessor="Apex Holdings LLC",
        lessee="Vertex Tech Solutions Corp",
        commencement_date=date(2024, 6, 1),
        expiration_date=date(2026, 5, 31),
        monthly_rent=Decimal("12500.00"),
        currency="AED",
        termination_notice_period_days=90,
    )
    client = Mock()
    client.responses.parse.return_value = SimpleNamespace(output_parsed=expected)
    monkeypatch.setattr(extraction, "_create_client", lambda: client)
    monkeypatch.setattr(extraction.settings, "openai_model", "test-model")

    result = extraction.extract_contract("Commercial lease text")

    assert result == expected
    client.responses.parse.assert_called_once_with(
        model="test-model",
        instructions=extraction.SYSTEM_INSTRUCTION,
        input="Commercial lease text",
        text_format=LLMExtractionCandidate,
    )
    assert "contract_duration_days" not in result.model_dump()


def test_extract_contract_rejects_missing_parsed_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock()
    client.responses.parse.return_value = SimpleNamespace(output_parsed=None)
    monkeypatch.setattr(extraction, "_create_client", lambda: client)
    monkeypatch.setattr(extraction.settings, "openai_model", "test-model")

    with pytest.raises(RuntimeError, match="did not return a structured extraction"):
        extraction.extract_contract("Commercial lease text")
