from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import datetime as dt
from typing import TYPE_CHECKING, Any

from app.core.money import cents_to_amount

if TYPE_CHECKING:
    from app.modules.finance.interfaces.api.schemas.transfer import TransferCreate, TransferOut


@dataclass
class CreateTransferRequest:
    user_id: int
    data: "TransferCreate"  # Forward reference to avoid circular import


@dataclass
class CreateTransferResponse:
    transfer: "TransferOut"  # Forward reference
    src_transaction_id: int
    dst_transaction_id: int


class CreateTransferUseCase:
    """Use case for creating transfers with fee calculations."""

    def __init__(self, transfer_crud: Any, transaction_crud: Any) -> None:
        self.transfer_crud = transfer_crud
        self.transaction_crud = transaction_crud

    async def execute(self, request: CreateTransferRequest) -> CreateTransferResponse:
        """Execute the create transfer use case."""
        # Create the transfer using CRUD
        tr, tx_out, tx_in = await self.transfer_crud.create_transfer(
            user_id=request.user_id, data=request.data
        )

        # Build the response DTO with calculated fees
        transfer_dto = self._build_transfer_dto(tr)
        return CreateTransferResponse(
            transfer=transfer_dto,
            src_transaction_id=tx_out.id,
            dst_transaction_id=tx_in.id
        )

    def _build_transfer_dto(self, transfer: Any) -> "TransferOut":
        """Build TransferOut DTO with calculated fees."""
        # Present amounts and rate in Decimals according to currency
        src_amount = cents_to_amount(transfer.src_amount_cents, transfer.rate_base)
        dst_amount = cents_to_amount(transfer.dst_amount_cents, transfer.rate_quote)

        # Build the base transfer DTO
        from app.modules.finance.interfaces.api.schemas.transfer import TransferOut
        out = TransferOut(
            id=transfer.id,
            src_account_id=transfer.src_account_id,
            dst_account_id=transfer.dst_account_id,
            src_amount=src_amount,
            dst_amount=dst_amount,
            rate_value=Decimal(str(transfer.rate_value)),
            rate_base=transfer.rate_base,
            rate_quote=transfer.rate_quote,
            occurred_at=transfer.occurred_at
            if transfer.occurred_at.tzinfo
            else transfer.occurred_at.replace(tzinfo=dt.timezone.utc),
            fx_rate_2dp=self._quantize_2dp(Decimal(str(transfer.rate_value))),
            vet_2dp=self._quantize_2dp(Decimal(str(transfer.vet_value)) if transfer.vet_value is not None else None),
            ref_rate_2dp=self._quantize_2dp(
                Decimal(str(transfer.ref_rate_value)) if transfer.ref_rate_value is not None else None
            ),
        )

        # Calculate fees derived preferencing reference FX when available
        base_fx = out.ref_rate_2dp or out.fx_rate_2dp
        if base_fx is not None and out.vet_2dp is not None and base_fx != 0:
            out.fees_per_unit_2dp = (out.vet_2dp - base_fx).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            out.fees_pct = ((out.vet_2dp / base_fx) - Decimal("1")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        return out

    @staticmethod
    def _quantize_2dp(value: Decimal | None) -> Decimal | None:
        """Quantize a decimal to 2 decimal places."""
        if value is None:
            return None
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)