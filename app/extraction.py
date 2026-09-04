from openai import (
    APIConnectionError,
    APIResponseValidationError,
    ContentFilterFinishReasonError,
    InternalServerError,
    LengthFinishReasonError,
    OpenAI,
    RateLimitError,
)
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.schemas import LLMExtractionCandidate


SYSTEM_INSTRUCTION = """You extract structured metadata from commercial real estate lease documents.

Extract information only from the supplied document.
Do not invent missing information.
Do not calculate contract duration.
Do not perform business validation or financial calculations.
Dates must represent the dates stated by the contract.
Currency must use its three-letter ISO code.
Termination notice must be represented in days.
Return data matching the provided schema."""

TRANSIENT_OPENAI_ERRORS = (APIConnectionError, RateLimitError, InternalServerError)
MALFORMED_RESPONSE_ERRORS = (
    APIResponseValidationError,
    ContentFilterFinishReasonError,
    LengthFinishReasonError,
)


class LLMUnavailableError(RuntimeError):
    pass


class LLMResponseError(RuntimeError):
    pass


def _create_client() -> OpenAI:
    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is required for contract extraction")
    return OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        max_retries=0,
        timeout=settings.llm_timeout_seconds,
    )


def extract_contract(raw_text: str) -> LLMExtractionCandidate:
    if not settings.openai_model:
        raise RuntimeError("OPENAI_MODEL is required for contract extraction")

    client = _create_client()
    try:
        for attempt in Retrying(
            stop=stop_after_attempt(settings.llm_max_retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(TRANSIENT_OPENAI_ERRORS),
            reraise=True,
        ):
            with attempt:
                response = client.responses.parse(
                    model=settings.openai_model,
                    instructions=SYSTEM_INSTRUCTION,
                    input=raw_text,
                    text_format=LLMExtractionCandidate,
                )
    except TRANSIENT_OPENAI_ERRORS as exc:
        raise LLMUnavailableError("OpenAI extraction service is unavailable") from exc
    except MALFORMED_RESPONSE_ERRORS as exc:
        raise LLMResponseError("OpenAI returned an unusable response") from exc

    if response.output_parsed is None:
        raise LLMResponseError("OpenAI did not return a structured extraction")
    return response.output_parsed
