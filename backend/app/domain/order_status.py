ORDER_STATUSES = {
    "DRAFT",
    "AWAITING_PAYMENT",
    "PAYMENT_EXPIRED",
    "CONFIRMED",
    "PREPARING",
    "READY_FOR_PICKUP",
    "OUT_FOR_DELIVERY",
    "COMPLETED",
    "CANCELLED",
}


ALLOWED_TRANSITIONS = {
    "DRAFT": {
        "AWAITING_PAYMENT",
        "CONFIRMED",
        "CANCELLED",
    },
    "AWAITING_PAYMENT": {
        "PAYMENT_EXPIRED",
        "CONFIRMED",
        "CANCELLED",
    },
    "PAYMENT_EXPIRED": {
        "AWAITING_PAYMENT",
        "CANCELLED",
    },
    "CONFIRMED": {
        "PREPARING",
        "CANCELLED",
    },
    "PREPARING": {
        "READY_FOR_PICKUP",
        "OUT_FOR_DELIVERY",
    },
    "READY_FOR_PICKUP": {
        "COMPLETED",
    },
    "OUT_FOR_DELIVERY": {
        "COMPLETED",
    },
    "COMPLETED": set(),
    "CANCELLED": set(),
}


def validate_order_status(status: str) -> None:
    if status not in ORDER_STATUSES:
        raise ValueError(
            f"Status de pedido inválido: {status}."
        )


def can_transition_order_status(
    current_status: str,
    new_status: str,
) -> bool:
    validate_order_status(current_status)
    validate_order_status(new_status)

    return new_status in ALLOWED_TRANSITIONS[current_status]


def validate_order_status_transition(
    current_status: str,
    new_status: str,
) -> None:
    if not can_transition_order_status(
        current_status,
        new_status,
    ):
        raise ValueError(
            f"Transição de {current_status} para "
            f"{new_status} não é permitida."
        )