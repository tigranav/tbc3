from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.blueprints.groups.models import BooksFilesGroup


class BooksFilesGroupRepository:
    def __init__(self, session: Session):
        self._session = session

    def list_groups(self) -> Iterable[BooksFilesGroup]:
        statement = select(BooksFilesGroup).order_by(BooksFilesGroup.id)
        return self._session.scalars(statement).all()

    def get_group(self, group_id: int) -> Optional[BooksFilesGroup]:
        return self._session.get(BooksFilesGroup, group_id)

    def create_group(self, *, group_id: int, name: str | None, comment: str | None) -> BooksFilesGroup:
        new_group = BooksFilesGroup(id=group_id, name=name, comment=comment)
        self._session.add(new_group)
        try:
            self._session.commit()
        except IntegrityError as exc:  # pragma: no cover - exercised via tests
            self._session.rollback()
            raise ValueError("Group with this id already exists") from exc
        return new_group

    def update_group(
        self, group_id: int, *, name: str | None = None, comment: str | None = None
    ) -> BooksFilesGroup | None:
        group = self.get_group(group_id)
        if group is None:
            return None
        group.name = name
        group.comment = comment
        self._session.add(group)
        self._session.commit()
        return group

    def delete_group(self, group_id: int) -> bool:
        group = self.get_group(group_id)
        if group is None:
            return False
        self._session.delete(group)
        self._session.commit()
        return True
