from sqlalchemy import Date, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
import datetime as dt

from app.models.base import Base, TimestampMixin


class FxRate(TimestampMixin, Base):
    __tablename__ = "fx_rates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    base: Mapped[str] = mapped_column(String(3), index=True)
    quote: Mapped[str] = mapped_column(String(3), index=True)
    rate_value: Mapped[float] = mapped_column(Numeric(18, 10))

    __table_args__ = (
        UniqueConstraint("date", "base", "quote", name="uq_fx_rates_date_base_quote"),
    )

