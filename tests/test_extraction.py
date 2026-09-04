from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai import APITimeoutError, AuthenticationError
from tenacity import wait_none

from app import extraction
from app.extraction import LLMResponseError, LLMUnavailableError
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

    with pytest.raises(LLMResponseError, match="did not return a structured extraction"):
        extraction.extract_contract("Commercial lease text")


def test_extract_contract_retries_transient_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = LLMExtractionCandidate(lessor="Apex Holdings LLC")
    client = Mock()
    client.responses.parse.side_effect = [
        APITimeoutError(request=Mock()),
        SimpleNamespace(output_parsed=expected),
    ]
    monkeypatch.setattr(extraction, "_create_client", lambda: client)
    monkeypatch.setattr(extraction.settings, "openai_model", "test-model")
    monkeypatch.setattr(extraction.settings, "llm_max_retries", 2)
    monkeypatch.setattr(extraction, "wait_exponential", lambda **_: wait_none())

    assert extraction.extract_contract("Commercial lease text") == expected
    assert client.responses.parse.call_count == 2


def test_extract_contract_does_not_retry_authentication_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = Mock()
    response.request = Mock()
    response.headers = {}
    client = Mock()
    client.responses.parse.side_effect = AuthenticationError(
        "Invalid API key",
        response=response,
        body=None,
    )
    monkeypatch.setattr(extraction, "_create_client", lambda: client)
    monkeypatch.setattr(extraction.settings, "openai_model", "test-model")
    monkeypatch.setattr(extraction.settings, "llm_max_retries", 2)
    monkeypatch.setattr(extraction, "wait_exponential", lambda **_: wait_none())

    with pytest.raises(AuthenticationError):
        extraction.extract_contract("Commercial lease text")

    client.responses.parse.assert_called_once()


def test_extract_contract_maps_exhausted_transient_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock()
    client.responses.parse.side_effect = APITimeoutError(request=Mock())
    monkeypatch.setattr(extraction, "_create_client", lambda: client)
    monkeypatch.setattr(extraction.settings, "openai_model", "test-model")
    monkeypatch.setattr(extraction.settings, "llm_max_retries", 2)
    monkeypatch.setattr(extraction, "wait_exponential", lambda **_: wait_none())

    with pytest.raises(LLMUnavailableError):
        extraction.extract_contract("Commercial lease text")

    assert client.responses.parse.call_count == 3
