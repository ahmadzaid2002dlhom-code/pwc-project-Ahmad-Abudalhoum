from collections.abc import Callable

from sqlalchemy.orm import Session

from app.database import create_contract
from app.extraction import extract_contract
from app.schemas import LLMExtractionCandidate, ValidatedContract


class ContractService:
    def __init__(
        self,
        db: Session,
        extractor: Callable[[str], LLMExtractionCandidate] = extract_contract,
    ) -> None:
        self.db = db
        self.extractor = extractor

    def process_contract(self, raw_text: str) -> ValidatedContract:
        candidate = self.extractor(raw_text)
        contract = ValidatedContract.model_validate(candidate.model_dump())
        create_contract(self.db, contract)
        return contract
