from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.blueprints.groups.models import BooksFilesGroup


class BooksFilesType(Base):
    __tablename__ = "books_files_types"
    __table_args__ = {"schema": "tbc"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(30))
    comments: Mapped[Optional[str]] = mapped_column(String(500))
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("tbc.books_files_groups.id"))

    group: Mapped[BooksFilesGroup] = relationship(BooksFilesGroup, lazy="joined")

    def to_dict(self) -> dict[str, int | str | None]:
        return {
            "id": self.id,
            "file_name": self.file_name,
            "comments": self.comments,
            "group_id": self.group_id,
            "group_name": self.group.name if self.group else None,
        }
