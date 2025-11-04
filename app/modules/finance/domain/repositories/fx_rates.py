from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Sequence

from app.modules.finance.domain.entities.fx_rate import FxRate


@dataclass(slots=True)
class FxRateUpsertData:
    base: str
    quote: str
    date: date
    rate_value: Decimal


class FxRateRepository(ABC):
    """Contrato para acesso a taxas de câmbio utilizadas pelo módulo finance."""

    @abstractmethod
    async def upsert(self, data: FxRateUpsertData) -> FxRate:
        ...

    @abstractmethod
    async def get_rate(
        self,
        base: str,
        quote: str,
        on_date: date,
    ) -> FxRate | None:
        ...

    @abstractmethod
    async def list_between(
        self,
        base: str,
        quote: str,
        date_from: date,
        date_to: date,
    ) -> Sequence[FxRate]:
        ...