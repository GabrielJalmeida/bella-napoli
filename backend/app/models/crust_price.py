from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CrustPrice(Base):
    __tablename__ = "crust_prices"

    __table_args__ = (
        CheckConstraint(
            "price >= 0",
            name="ck_crust_prices_price_non_negative",
        ),
        CheckConstraint(
            "size IN ('P', 'M', 'G')",
            name="ck_crust_prices_size_valid",
        ),
        UniqueConstraint(
            "crust_id",
            "size",
            name="uq_crust_prices_crust_size",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    crust_id: Mapped[int] = mapped_column(
        ForeignKey("crusts.id"),
        nullable=False,
    )

    size: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )