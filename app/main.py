from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import Base, ContractRecord, engine, get_contract, get_db, list_contracts
from app.extraction import LLMResponseError, LLMUnavailableError
from app.schemas import ContractExtractionRequest, ContractResponse
from app.service import ContractService


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Lease Contract Extraction API",
    description="Extract, validate, store, and retrieve commercial lease metadata.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/v1/extract",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
)
def extract_contract(
    request: ContractExtractionRequest,
    db: Session = Depends(get_db),
) -> ContractRecord:
    try:
        return ContractService(db).process_contract(request.text)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.errors(
                include_url=False,
                include_context=False,
                include_input=False,
            ),
        ) from exc
    except LLMUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Contract extraction service is temporarily unavailable",
        ) from exc
    except LLMResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Contract extraction service returned an unusable response",
        ) from exc


@app.get("/api/v1/contracts", response_model=list[ContractResponse])
def get_contracts(db: Session = Depends(get_db)) -> list[ContractRecord]:
    return list_contracts(db)


@app.get("/api/v1/contracts/{contract_id}", response_model=ContractResponse)
def get_contract_by_id(
    contract_id: int,
    db: Session = Depends(get_db),
) -> ContractRecord:
    contract = get_contract(db, contract_id)
    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )
    return contract


frontend_directory = Path("frontend/dist")
if frontend_directory.is_dir():
    app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")
