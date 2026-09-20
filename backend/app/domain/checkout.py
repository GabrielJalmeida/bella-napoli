from decimal import Decimal


DELIVERY_METHODS = {
    "DELIVERY",
    "PICKUP",
}

PAYMENT_METHODS = {
    "PIX_DEMO",
    "CREDIT_ON_DELIVERY",
    "DEBIT_ON_DELIVERY",
    "CASH",
}


def validate_delivery_method(delivery_method: str) -> None:
    if delivery_method not in DELIVERY_METHODS:
        raise ValueError(
            "Método de entrega inválido."
        )


def validate_delivery_data(
    delivery_method: str,
    delivery_neighborhood: str | None,
    delivery_zip_code: str | None,
    delivery_street: str | None,
    delivery_number: str | None,
) -> None:
    validate_delivery_method(delivery_method)

    if delivery_method == "PICKUP":
        if any(
            value is not None
            for value in (
                delivery_neighborhood,
                delivery_zip_code,
                delivery_street,
                delivery_number,
            )
        ):
            raise ValueError(
                "Pedidos para retirada não devem possuir endereço de entrega."
            )

        return

    required_fields = {
        "bairro": delivery_neighborhood,
        "CEP": delivery_zip_code,
        "rua": delivery_street,
        "número": delivery_number,
    }

    for field_name, value in required_fields.items():
        if value is None or not value.strip():
            raise ValueError(
                f"O campo {field_name} é obrigatório para entrega."
            )


def validate_checkout_payment(
    payment_method: str,
    order_total: Decimal,
    change_for: Decimal | None = None,
) -> None:
    if payment_method not in PAYMENT_METHODS:
        raise ValueError(
            "Método de pagamento inválido."
        )

    if order_total <= 0:
        raise ValueError(
            "O pedido precisa possuir um total maior que zero."
        )

    if payment_method == "CASH":
        if change_for is not None and change_for <= order_total:
            raise ValueError(
                "O valor informado para troco deve ser maior que o total do pedido."
            )

    elif change_for is not None:
        raise ValueError(
            "Troco somente pode ser informado para pagamento em dinheiro."
        )


def validate_customer_data(
    name: str,
    phone: str,
) -> None:
    if not name or not name.strip():
        raise ValueError(
            "O nome do cliente é obrigatório."
        )

    if not phone or not phone.strip():
        raise ValueError(
            "O telefone do cliente é obrigatório."
        )


def validate_order_has_items(
    item_count: int,
) -> None:
    if item_count <= 0:
        raise ValueError(
            "Não é possível finalizar um pedido sem itens."
        )