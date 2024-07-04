from typing import (
    List,
    Optional,
)
from datetime import datetime

from sqlalchemy import (
    ForeignKey,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class TiebaBase(DeclarativeBase):
    pass


class TiebaPost(TiebaBase):
    __tablename__ = "tieba_post"

    pid: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str]
    title: Mapped[str]
    died: Mapped[bool] = mapped_column(default=False)

    comments: Mapped[List["TiebaComment"]] = relationship(back_populates="post")
    lifeline: Mapped[List["TiebaTotal"]] = relationship(back_populates="post")

    def __repr__(self) -> str:
        return (
            f"TiebaPost(pid={self.pid!r}, "
            f"title={self.title!r}, "
            f"died={self.died!r})"
        )


class TiebaComment(TiebaBase):
    __tablename__ = "tieba_comment"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str]
    floor: Mapped[int]
    time: Mapped[datetime]
    uid: Mapped[Optional[int]]
    uname: Mapped[str]
    pid: Mapped[int] = mapped_column(ForeignKey("tieba_post.pid"))

    post: Mapped["TiebaPost"] = relationship(back_populates="comments")

    def __repr__(self) -> str:
        return (
            f"TiebaComment(id={self.id!r}, "
            f"text={self.text!r}, "
            f"floor={self.floor!r}, "
            f"time={self.time!r}, "
            f"post={self.post!r})"
        )


class TiebaTotal(TiebaBase):
    __tablename__ = "tieba_total"

    id: Mapped[int] = mapped_column(primary_key=True)
    total: Mapped[int] = mapped_column(default=0)
    time: Mapped[datetime] = mapped_column(default=datetime.now)
    pid: Mapped[int] = mapped_column(ForeignKey("tieba_post.pid"))

    post: Mapped["TiebaPost"] = relationship(back_populates="lifeline")

    def __repr__(self):
        return (
            f"TiebaTotal(id={self.id!r}, "
            f"total={self.total!r}, "
            f"time={self.time!r}, "
            f"post={self.post!r})"
        )
