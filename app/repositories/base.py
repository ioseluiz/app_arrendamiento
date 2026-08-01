from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id_: int) -> ModelType | None:
        return self.session.get(self.model, id_)

    def list(self) -> list[ModelType]:
        return list(self.session.scalars(select(self.model)))

    def add(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        self.session.flush()
        return obj

    def delete(self, obj: ModelType) -> None:
        self.session.delete(obj)
        self.session.flush()
