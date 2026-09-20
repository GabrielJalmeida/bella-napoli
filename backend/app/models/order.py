from decimal import Decimal
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint(
            "subtotal >= 0",
            name="ck_orders_subtotal_non_negative",
        ),
        CheckConstraint(
            "delivery_fee >= 0",
            name="ck_orders_delivery_fee_non_negative",
        ),
        CheckConstraint(
            "total >= 0",
            name="ck_orders_total_non_negative",
        ),
        CheckConstraint(
            "status IN ("
            "'DRAFT', "
            "'AWAITING_PAYMENT', "
            "'PAYMENT_EXPIRED', "
            "'CONFIRMED', "
            "'PREPARING', "
            "'READY_FOR_PICKUP', "
            "'OUT_FOR_DELIVERY', "
            "'COMPLETED', "
            "'CANCELLED'"
            ")",
            name="ck_orders_status_valid",
        ),
        CheckConstraint(
            "delivery_method IS NULL "
            "OR delivery_method IN ('DELIVERY', 'PICKUP')",
            name="ck_orders_delivery_method_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DRAFT",
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    delivery_method: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    delivery_neighborhood: Mapped[str | None] = mapped_column(
    String(80),
    nullable=True,
)

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"),
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

    delivery_zip_code: Mapped[str | None] = mapped_column(
        String(9),
        nullable=True,
    )

    delivery_street: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    delivery_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    delivery_complement: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    delivery_reference: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )