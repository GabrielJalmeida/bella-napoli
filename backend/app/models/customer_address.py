from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"

    id: Mapped[int] = mapped_column(primary_key=True)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )

    zip_code: Mapped[str] = mapped_column(
        String(9),
        nullable=False,
    )

    street: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    complement: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    neighborhood: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    reference: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )