from decimal import Decimal
from app.core.events.base import DomainEvent

class TransferCreated(DomainEvent):
    def __init__(self, user_id: int, from_account_id: int, to_account_id: int, amount_sent: Decimal, amount_received: Decimal):
        super().__init__()
        self.user_id = user_id
        self.from_account_id = from_account_id
        self.to_account_id = to_account_id
        self.amount_sent = amount_sent
        self.amount_received = amount_received
        self.type = "finance.transfer.created"