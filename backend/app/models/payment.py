from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint(
            "method IN ("
            "'PIX_DEMO', "
            "'CREDIT_ON_DELIVERY', "
            "'DEBIT_ON_DELIVERY', "
            "'CASH'"
            ")",
            name="ck_payments_method_valid",
        ),
        CheckConstraint(
            "status IN ("
            "'PENDING', "
            "'PAID', "
            "'EXPIRED', "
            "'CANCELLED'"
            ")",
            name="ck_payments_status_valid",
        ),
        CheckConstraint(
            "amount >= 0",
            name="ck_payments_amount_non_negative",
        ),
        CheckConstraint(
            "change_for IS NULL OR change_for > amount",
            name="ck_payments_change_for_valid",
        ),
        UniqueConstraint(
            "pix_token",
            name="uq_payments_pix_token",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
    )

    method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    change_for: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    pix_token: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )