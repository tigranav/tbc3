from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BooksFilesGroup(Base):
    __tablename__ = "books_files_groups"
    __table_args__ = {"schema": "tbc"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(50))
    comment: Mapped[Optional[str]] = mapped_column(String(200))

    def to_dict(self) -> dict[str, Optional[str | int]]:
        return {"id": self.id, "name": self.name, "comment": self.comment}
