from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.engine import Base


class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    __table_args__ = (
        UniqueConstraint("user_id", "title", name="uq_wishlist_user_title"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    authors: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    thumbnail: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    info_link: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="wishlist")  # noqa: F821

    def __repr__(self) -> str:
        return f"<WishlistItem id={self.id} user_id={self.user_id} title={self.title!r}>"