from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

ModelType = TypeVar("ModelType")

class BaseRepository(ABC, Generic[ModelType]):
    @abstractmethod
    async def get(self, id: Any) -> Optional[ModelType]:
        pass

    @abstractmethod
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        pass

    @abstractmethod
    async def create(self, obj_in: ModelType) -> ModelType:
        pass

    @abstractmethod
    async def update(self, db_obj: ModelType, obj_in: ModelType) -> ModelType:
        pass

    @abstractmethod
    async def remove(self, id: Any) -> Optional[ModelType]:
        pass
