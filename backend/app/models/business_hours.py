from datetime import time

from sqlalchemy import Boolean, CheckConstraint, SmallInteger, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BusinessHours(Base):
    __tablename__ = "business_hours"

    __table_args__ = (
        CheckConstraint(
            "day_of_week BETWEEN 0 AND 6",
            name="ck_business_hours_day_of_week_valid",
        ),
        UniqueConstraint(
            "day_of_week",
            name="uq_business_hours_day_of_week",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # 0 = segunda ... 6 = domingo
    day_of_week: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    open_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    close_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )