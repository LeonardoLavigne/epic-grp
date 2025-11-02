from sqlalchemy import String, ForeignKey, BigInteger, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column
import datetime as dt

from app.models.base import Base, TimestampMixin


class Transfer(TimestampMixin, Base):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    src_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"))
    dst_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"))

    src_amount_cents: Mapped[int] = mapped_column(BigInteger)
    dst_amount_cents: Mapped[int] = mapped_column(BigInteger)

    rate_base: Mapped[str] = mapped_column(String(3))
    rate_quote: Mapped[str] = mapped_column(String(3))
    rate_value: Mapped[float] = mapped_column(Numeric(18, 10))

    occurred_at: Mapped[dt.datetime]
    voided: Mapped[bool] = mapped_column(Boolean, default=False)
