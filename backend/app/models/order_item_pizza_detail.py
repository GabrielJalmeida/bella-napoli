from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OrderItemPizzaDetail(Base):
    __tablename__ = "order_item_pizza_details"

    __table_args__ = (
        UniqueConstraint(
            "order_item_id",
            name="uq_order_item_pizza_details_order_item",
        ),
        CheckConstraint(
            "crust_price >= 0",
            name="ck_order_item_pizza_details_crust_price_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id"),
        nullable=False,
    )

    crust_id: Mapped[int | None] = mapped_column(
        ForeignKey("crusts.id"),
        nullable=True,
    )

    crust_name: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    crust_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )