from decimal import Decimal

import pytest

from app.domain.payment import (
    validate_cash_payment,
    validate_payment_amount,
    validate_payment_method,
    validate_payment_status,
)


def test_validate_payment_method_accepts_valid_method():
    validate_payment_method("PIX_DEMO")


def test_validate_payment_method_rejects_invalid_method():
    with pytest.raises(ValueError):
        validate_payment_method("BOLETO")


def test_validate_payment_status_accepts_valid_status():
    validate_payment_status("PENDING")


def test_validate_payment_status_rejects_invalid_status():
    with pytest.raises(ValueError):
        validate_payment_status("UNKNOWN")


def test_validate_payment_amount_accepts_zero():
    validate_payment_amount(Decimal("0.00"))


def test_validate_payment_amount_rejects_negative():
    with pytest.raises(ValueError):
        validate_payment_amount(Decimal("-1.00"))


def test_validate_cash_payment_without_change_is_valid():
    validate_cash_payment(
        amount=Decimal("57.80"),
        change_for=None,
    )


def test_validate_cash_payment_with_higher_value_is_valid():
    validate_cash_payment(
        amount=Decimal("57.80"),
        change_for=Decimal("100.00"),
    )


def test_validate_cash_payment_rejects_equal_value():
    with pytest.raises(ValueError):
        validate_cash_payment(
            amount=Decimal("57.80"),
            change_for=Decimal("57.80"),
        )


def test_validate_cash_payment_rejects_lower_value():
    with pytest.raises(ValueError):
        validate_cash_payment(
            amount=Decimal("57.80"),
            change_for=Decimal("50.00"),
        )