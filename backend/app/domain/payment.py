from decimal import Decimal


PAYMENT_METHODS = {
    "PIX_DEMO",
    "CREDIT_ON_DELIVERY",
    "DEBIT_ON_DELIVERY",
    "CASH",
}

PAYMENT_STATUSES = {
    "PENDING",
    "PAID",
    "EXPIRED",
    "CANCELLED",
}


def validate_payment_method(method: str) -> None:
    if method not in PAYMENT_METHODS:
        raise ValueError(f"Método de pagamento inválido: {method}")


def validate_payment_status(status: str) -> None:
    if status not in PAYMENT_STATUSES:
        raise ValueError(f"Status de pagamento inválido: {status}")


def validate_cash_payment(
    amount: Decimal,
    change_for: Decimal | None,
) -> None:
    if amount < 0:
        raise ValueError("O valor do pagamento não pode ser negativo.")

    if change_for is None:
        return

    if change_for <= amount:
        raise ValueError(
            "O valor informado para troco deve ser maior que o total do pedido."
        )


def validate_payment_amount(amount: Decimal) -> None:
    if amount < 0:
        raise ValueError("O valor do pagamento não pode ser negativo.")