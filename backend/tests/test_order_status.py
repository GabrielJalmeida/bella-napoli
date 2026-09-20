import pytest

from app.domain.order_status import (
    can_transition_order_status,
    validate_order_status,
    validate_order_status_transition,
)


def test_valid_order_transitions():
    assert can_transition_order_status(
        "DRAFT",
        "CONFIRMED",
    )

    assert can_transition_order_status(
        "CONFIRMED",
        "PREPARING",
    )

    assert can_transition_order_status(
        "PREPARING",
        "OUT_FOR_DELIVERY",
    )

    assert can_transition_order_status(
        "OUT_FOR_DELIVERY",
        "COMPLETED",
    )


def test_invalid_order_transitions():
    assert not can_transition_order_status(
        "DRAFT",
        "COMPLETED",
    )

    assert not can_transition_order_status(
        "COMPLETED",
        "PREPARING",
    )

    assert not can_transition_order_status(
        "CANCELLED",
        "CONFIRMED",
    )


def test_terminal_statuses_cannot_transition():
    assert not can_transition_order_status(
        "COMPLETED",
        "COMPLETED",
    )

    assert not can_transition_order_status(
        "CANCELLED",
        "CANCELLED",
    )


def test_payment_expired_can_retry_payment():
    assert can_transition_order_status(
        "PAYMENT_EXPIRED",
        "AWAITING_PAYMENT",
    )


def test_invalid_status_is_rejected():
    with pytest.raises(
        ValueError,
        match="Status de pedido inválido",
    ):
        validate_order_status("INVALID")


def test_invalid_transition_raises_error():
    with pytest.raises(
        ValueError,
        match="não é permitida",
    ):
        validate_order_status_transition(
            "DRAFT",
            "COMPLETED",
        )