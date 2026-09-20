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


class OrderItemPizzaFlavor(Base):
    __tablename__ = "order_item_pizza_flavors"

    __table_args__ = (
        UniqueConstraint(
            "order_item_id",
            "slot",
            name="uq_order_item_pizza_flavors_item_slot",
        ),
        CheckConstraint(
            "slot IN (1, 2)",
            name="ck_order_item_pizza_flavors_slot_valid",
        ),
        CheckConstraint(
            "fraction IN (0.5, 1.0)",
            name="ck_order_item_pizza_flavors_fraction_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id"),
        nullable=False,
    )

    flavor_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
    )

    flavor_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    slot: Mapped[int] = mapped_column(
        nullable=False,
    )

    fraction: Mapped[Decimal] = mapped_column(
        Numeric(2, 1),
        nullable=False,
    )