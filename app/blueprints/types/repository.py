from __future__ import annotations

from typing import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.blueprints.groups.models import BooksFilesGroup
from app.blueprints.types.models import BooksFilesType


class BooksFilesTypeRepository:
    def __init__(self, session: Session):
        self._session = session

    def list_types(self) -> Iterable[BooksFilesType]:
        statement = select(BooksFilesType).order_by(BooksFilesType.id)
        return self._session.scalars(statement).all()

    def get_type(self, type_id: int) -> Optional[BooksFilesType]:
        return self._session.get(BooksFilesType, type_id)

    def _get_group(self, group_id: int) -> BooksFilesGroup | None:
        return self._session.get(BooksFilesGroup, group_id)

    def _ensure_group(self, group_id: int) -> BooksFilesGroup:
        group = self._get_group(group_id)
        if group is None:
            raise ValueError("Связанная группа не найдена")
        return group

    def create_type(
        self,
        *,
        type_id: int,
        file_name: str | None,
        comments: str | None,
        group_id: int,
    ) -> BooksFilesType:
        self._ensure_group(group_id)
        new_type = BooksFilesType(
            id=type_id, file_name=file_name, comments=comments, group_id=group_id
        )
        self._session.add(new_type)
        try:
            self._session.commit()
        except IntegrityError as exc:  # pragma: no cover - exercised via tests
            self._session.rollback()
            raise ValueError("Запись с таким id уже существует") from exc
        self._session.refresh(new_type)
        return new_type

    def update_type(
        self,
        type_id: int,
        *,
        file_name: str | None = None,
        comments: str | None = None,
        group_id: int | None = None,
    ) -> BooksFilesType | None:
        existing = self.get_type(type_id)
        if existing is None:
            return None

        if group_id is not None:
            self._ensure_group(group_id)
            existing.group_id = group_id

        existing.file_name = file_name
        existing.comments = comments
        self._session.add(existing)
        self._session.commit()
        self._session.refresh(existing)
        return existing

    def delete_type(self, type_id: int) -> bool:
        existing = self.get_type(type_id)
        if existing is None:
            return False
        self._session.delete(existing)
        self._session.commit()
        return True
