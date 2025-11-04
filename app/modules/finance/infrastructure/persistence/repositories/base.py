from typing import TypeVar, Any

from app.core.persistence.sqlalchemy_repository import SQLAlchemyRepository
from app.db.base import Base as BaseModel

FinanceModelType = TypeVar("FinanceModelType", bound=BaseModel)

class FinanceRepository(SQLAlchemyRepository[FinanceModelType, Any, Any]):
    pass
