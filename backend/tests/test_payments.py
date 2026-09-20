from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.database import engine

import pytest

from app.services.orders import create_draft_order
from app.services.payments import (
    confirm_pix_payment,
    create_payment_attempt,
    expire_pix_payment,
)

@pytest.fixture
def session():
    session = Session(engine)

    try:
        yield session
    finally:
        session.rollback()
        session.close()

def create_test_order(session):
    order = create_draft_order(session)

    order.subtotal = Decimal("57.80")
    order.delivery_fee = Decimal("0.00")
    order.total = Decimal("57.80")

    session.flush()

    return order


def test_create_pix_payment(session):
    order = create_test_order(session)

    payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method="PIX_DEMO",
    )

    assert payment.order_id == order.id
    assert payment.method == "PIX_DEMO"
    assert payment.status == "PENDING"
    assert payment.amount == Decimal("57.80")

    assert payment.pix_token is not None
    assert len(payment.pix_token) > 0

    assert payment.expires_at is not None

    now = datetime.now(timezone.utc)
    remaining = payment.expires_at - now

    assert remaining.total_seconds() > 290
    assert remaining.total_seconds() <= 300


def test_create_credit_payment(session):
    order = create_test_order(session)

    payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method="CREDIT_ON_DELIVERY",
    )

    assert payment.method == "CREDIT_ON_DELIVERY"
    assert payment.status == "PENDING"
    assert payment.amount == Decimal("57.80")
    assert payment.pix_token is None
    assert payment.expires_at is None


def test_create_debit_payment(session):
    order = create_test_order(session)

    payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method="DEBIT_ON_DELIVERY",
    )

    assert payment.method == "DEBIT_ON_DELIVERY"
    assert payment.status == "PENDING"
    assert payment.amount == Decimal("57.80")
    assert payment.pix_token is None
    assert payment.expires_at is None


def test_create_cash_payment(session):
    order = create_test_order(session)

    payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method="CASH",
        change_for=Decimal("100.00"),
    )

    assert payment.method == "CASH"
    assert payment.status == "PENDING"
    assert payment.amount == Decimal("57.80")
    assert payment.change_for == Decimal("100.00")
    assert payment.pix_token is None
    assert payment.expires_at is None


def test_non_cash_payment_rejects_change_for(session):
    order = create_test_order(session)

    with pytest.raises(ValueError):
        create_payment_attempt(
            session=session,
            order_id=order.id,
            method="PIX_DEMO",
            change_for=Decimal("100.00"),
        )


def test_cash_payment_rejects_invalid_change(session):
    order = create_test_order(session)

    with pytest.raises(ValueError):
        create_payment_attempt(
            session=session,
            order_id=order.id,
            method="CASH",
            change_for=Decimal("50.00"),
        )


def test_payment_amount_comes_from_order(session):
    order = create_test_order(session)

    payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method="CREDIT_ON_DELIVERY",
    )

    assert payment.amount == order.total

def test_confirm_pix_payment_changes_pending_to_paid(session: Session):
    order = create_test_order(session)

    payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method="PIX_DEMO",
    )

    confirmed = confirm_pix_payment(
        session=session,
        pix_token=payment.pix_token,
    )

    assert confirmed.status == "PAID"
    assert confirmed.paid_at is not None


def test_confirm_pix_payment_is_idempotent(session: Session):
    order = create_test_order(session)

    payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method="PIX_DEMO",
    )

    first_confirmation = confirm_pix_payment(
        session=session,
        pix_token=payment.pix_token,
    )

    first_paid_at = first_confirmation.paid_at

    second_confirmation = confirm_pix_payment(
        session=session,
        pix_token=payment.pix_token,
    )

    assert first_confirmation.id == second_confirmation.id
    assert second_confirmation.status == "PAID"
    assert second_confirmation.paid_at == first_paid_at


def test_confirm_pix_payment_expires_when_time_is_over(session: Session):
    order = create_test_order(session)

    payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method="PIX_DEMO",
    )

    payment.expires_at = (
        datetime.now(timezone.utc)
        - timedelta(seconds=1)
    )

    session.flush()

    with pytest.raises(ValueError, match="expirou"):
        confirm_pix_payment(
            session=session,
            pix_token=payment.pix_token,
        )

    assert payment.status == "EXPIRED"


def test_expire_pix_payment_changes_pending_to_expired(session: Session):
    order = create_test_order(session)

    payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method="PIX_DEMO",
    )

    payment.expires_at = (
        datetime.now(timezone.utc)
        - timedelta(seconds=1)
    )

    session.flush()

    expired = expire_pix_payment(
        session=session,
        payment_id=payment.id,
    )

    assert expired.status == "EXPIRED"


def test_expired_pix_allows_new_payment_attempt(session: Session):
    order = create_test_order(session)

    first_payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method="PIX_DEMO",
    )

    first_payment.expires_at = (
        datetime.now(timezone.utc)
        - timedelta(seconds=1)
    )

    session.flush()

    expire_pix_payment(
        session=session,
        payment_id=first_payment.id,
    )

    second_payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method="PIX_DEMO",
    )

    assert first_payment.status == "EXPIRED"
    assert second_payment.status == "PENDING"
    assert second_payment.id != first_payment.id
    assert second_payment.pix_token != first_payment.pix_token