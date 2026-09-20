from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DeliveryZone(Base):
    __tablename__ = "delivery_zones"

    __table_args__ = (
        CheckConstraint(
            "fee >= 0",
            name="ck_delivery_zones_fee_non_negative",
        ),
        UniqueConstraint(
            "neighborhood",
            name="uq_delivery_zones_neighborhood",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    neighborhood: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )