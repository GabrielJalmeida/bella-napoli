from decimal import Decimal, ROUND_HALF_UP


MONEY_QUANTUM = Decimal("0.01")


def _normalize_money(value: Decimal) -> Decimal:
    return value.quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def calculate_pizza_price(
    first_half_price: Decimal,
    second_half_price: Decimal | None = None,
) -> Decimal:
    """
    Calcula o preço base de uma pizza.

    Pizza inteira:
        calculate_pizza_price(Decimal("52.90"))
        -> 52.90

    Meio a meio:
        calculate_pizza_price(
            Decimal("52.90"),
            Decimal("54.90"),
        )
        -> 53.90

    Mesmo sabor nas duas metades:
        calculate_pizza_price(
            Decimal("52.90"),
            Decimal("52.90"),
        )
        -> 52.90
    """

    if first_half_price < 0:
        raise ValueError(
            "O preço da primeira metade não pode ser negativo."
        )

    if second_half_price is None:
        return _normalize_money(first_half_price)

    if second_half_price < 0:
        raise ValueError(
            "O preço da segunda metade não pode ser negativo."
        )

    price = (
        first_half_price + second_half_price
    ) / Decimal("2")

    return _normalize_money(price)


def calculate_pizza_total(
    pizza_price: Decimal,
    crust_price: Decimal | None = None,
) -> Decimal:
    """
    Calcula o total de uma pizza considerando,
    opcionalmente, a borda.
    """

    if pizza_price < 0:
        raise ValueError(
            "O preço da pizza não pode ser negativo."
        )

    if crust_price is not None and crust_price < 0:
        raise ValueError(
            "O preço da borda não pode ser negativo."
        )

    total = pizza_price

    if crust_price is not None:
        total += crust_price

    return _normalize_money(total)


DELIVERY_FEES = {
    "Mooca": Decimal("4.90"),
    "Belém": Decimal("5.90"),
    "Brás": Decimal("6.90"),
    "Água Rasa": Decimal("6.90"),
    "Tatuapé": Decimal("7.90"),
}


def calculate_item_total(
    unit_price: Decimal,
    quantity: int,
) -> Decimal:
    if unit_price < 0:
        raise ValueError(
            "O preço unitário não pode ser negativo."
        )

    if quantity <= 0:
        raise ValueError(
            "A quantidade deve ser maior que zero."
        )

    total = unit_price * quantity

    return _normalize_money(total)


def calculate_delivery_fee(
    delivery_method: str,
    neighborhood: str | None = None,
    delivery_fee: Decimal | None = None,
) -> Decimal:
    """
    Calcula a taxa de entrega.

    PICKUP:
        taxa zero.

    DELIVERY:
        pode receber uma taxa já encontrada no banco.

        Caso nenhuma taxa seja fornecida, usa temporariamente
        DELIVERY_FEES como fallback para manter os testes
        do domínio independentes do banco.
    """

    if delivery_method == "PICKUP":
        return Decimal("0.00")

    if delivery_method != "DELIVERY":
        raise ValueError(
            "Método de entrega inválido."
        )

    if delivery_fee is not None:
        if delivery_fee < 0:
            raise ValueError(
                "A taxa de entrega não pode ser negativa."
            )

        return _normalize_money(delivery_fee)

    if not neighborhood:
        raise ValueError(
            "O bairro é obrigatório para entrega."
        )

    neighborhood = neighborhood.strip()

    fee = DELIVERY_FEES.get(neighborhood)

    if fee is None:
        raise ValueError(
            "Bairro não atendido para entrega."
        )

    return _normalize_money(fee)


def calculate_order_total(
    item_totals: list[Decimal],
    delivery_fee: Decimal = Decimal("0.00"),
) -> Decimal:
    """
    Calcula o total do pedido a partir dos totais
    dos itens e da taxa de entrega.
    """

    if delivery_fee < 0:
        raise ValueError(
            "A taxa de entrega não pode ser negativa."
        )

    subtotal = Decimal("0.00")

    for item_total in item_totals:
        if item_total < 0:
            raise ValueError(
                "O valor de um item não pode ser negativo."
            )

        subtotal += item_total

    return _normalize_money(
        subtotal + delivery_fee
    )