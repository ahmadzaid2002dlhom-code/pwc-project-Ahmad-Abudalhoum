from collections.abc import Generator
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import settings
from app.schemas import ValidatedContract


class Base(DeclarativeBase):
    pass


class ContractRecord(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    lessor: Mapped[str] = mapped_column(String)
    lessee: Mapped[str] = mapped_column(String)
    commencement_date: Mapped[date] = mapped_column(Date)
    expiration_date: Mapped[date] = mapped_column(Date)
    monthly_rent: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    termination_notice_period_days: Mapped[int] = mapped_column(Integer)


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def create_contract(db: Session, contract: ValidatedContract) -> ContractRecord:
    if not isinstance(contract, ValidatedContract):
        raise TypeError("contract must be a ValidatedContract")

    record = ContractRecord(
        lessor=contract.lessor,
        lessee=contract.lessee,
        commencement_date=contract.commencement_date,
        expiration_date=contract.expiration_date,
        monthly_rent=contract.monthly_rent,
        currency=contract.currency,
        termination_notice_period_days=contract.termination_notice_period_days,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_contracts(db: Session) -> list[ContractRecord]:
    return list(db.scalars(select(ContractRecord).order_by(ContractRecord.id)))


def get_contract(db: Session, contract_id: int) -> ContractRecord | None:
    return db.get(ContractRecord, contract_id)
