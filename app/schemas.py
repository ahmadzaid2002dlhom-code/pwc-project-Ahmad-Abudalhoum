from datetime import date
from decimal import Decimal
from typing import Annotated, Self

from iso4217 import Currency
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    WithJsonSchema,
    computed_field,
    field_validator,
    model_validator,
)


class ContractExtractionRequest(BaseModel):
    text: str = Field(min_length=1)


class LLMExtractionCandidate(BaseModel):
    lessor: str | None = None
    lessee: str | None = None
    commencement_date: date | None = None
    expiration_date: date | None = None
    monthly_rent: Annotated[
        Decimal | None,
        WithJsonSchema({"anyOf": [{"type": "number"}, {"type": "null"}]}),
    ] = None
    currency: str | None = None
    termination_notice_period_days: int | None = None


class ValidatedContract(BaseModel):
    lessor: str
    lessee: str
    commencement_date: date
    expiration_date: date
    monthly_rent: Decimal = Field(ge=0)
    currency: str
    termination_notice_period_days: int

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in Currency.__members__:
            raise ValueError("currency must be a valid ISO 4217 code")
        return normalized

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if self.expiration_date < self.commencement_date:
            raise ValueError("expiration_date must not be before commencement_date")
        return self

    @computed_field
    @property
    def contract_duration_days(self) -> int:
        return (self.expiration_date - self.commencement_date).days


class ContractResponse(ValidatedContract):
    model_config = ConfigDict(from_attributes=True)

    id: int
