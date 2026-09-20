from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


ORDER_STATUSES = (
    "DRAFT",
    "AWAITING_PAYMENT",
    "PAYMENT_EXPIRED",
    "CONFIRMED",
    "PREPARING",
    "READY_FOR_PICKUP",
    "OUT_FOR_DELIVERY",
    "COMPLETED",
    "CANCELLED",
)


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    __table_args__ = (
        CheckConstraint(
            "to_status IN ("
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
            name="ck_order_status_history_to_status_valid",
        ),
        CheckConstraint(
            "from_status IS NULL OR from_status IN ("
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
            name="ck_order_status_history_from_status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
    )

    from_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    to_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )