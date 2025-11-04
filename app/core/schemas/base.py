from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IDModel(ORMBase):
    id: int


class PageParams(BaseModel):
    skip: int = 0
    limit: int = 100

