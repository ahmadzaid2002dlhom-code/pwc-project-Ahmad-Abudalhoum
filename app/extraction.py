from openai import OpenAI

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


def _create_client() -> OpenAI:
    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is required for contract extraction")
    return OpenAI(api_key=settings.openai_api_key.get_secret_value())


def extract_contract(raw_text: str) -> LLMExtractionCandidate:
    if not settings.openai_model:
        raise RuntimeError("OPENAI_MODEL is required for contract extraction")

    response = _create_client().responses.parse(
        model=settings.openai_model,
        instructions=SYSTEM_INSTRUCTION,
        input=raw_text,
        text_format=LLMExtractionCandidate,
    )

    if response.output_parsed is None:
        raise RuntimeError("OpenAI did not return a structured extraction")
    return response.output_parsed
