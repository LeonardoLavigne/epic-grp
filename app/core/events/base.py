from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class DomainEvent:
    event_id: str = str(uuid.uuid4())
    occurred_on: datetime = datetime.now()
    type: str = ""