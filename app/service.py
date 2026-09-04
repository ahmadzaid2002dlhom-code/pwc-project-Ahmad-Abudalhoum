from collections.abc import Callable

from sqlalchemy.orm import Session

from app.database import ContractRecord, create_contract
from app.extraction import extract_contract
from app.schemas import LLMExtractionCandidate, ValidatedContract


class ContractService:
    def __init__(
        self,
        db: Session,
        extractor: Callable[[str], LLMExtractionCandidate] | None = None,
    ) -> None:
        self.db = db
        self.extractor = extractor if extractor is not None else extract_contract

    def process_contract(self, raw_text: str) -> ContractRecord:
        candidate = self.extractor(raw_text)
        contract = ValidatedContract.model_validate(candidate.model_dump())
        return create_contract(self.db, contract)
