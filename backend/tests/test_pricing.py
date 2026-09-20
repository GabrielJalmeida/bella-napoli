from decimal import Decimal

import pytest

from app.domain.pricing import (
    calculate_delivery_fee,
    calculate_item_total,
    calculate_order_total,
    calculate_pizza_price,
    calculate_pizza_total,
)


def test_pizza_inteira():
    result = calculate_pizza_price(
        Decimal("52.90"),
    )

    assert result == Decimal("52.90")


def test_pizza_meio_a_meio():
    result = calculate_pizza_price(
        Decimal("52.90"),
        Decimal("54.90"),
    )

    assert result == Decimal("53.90")


def test_mesmo_sabor_nas_duas_metades():
    result = calculate_pizza_price(
        Decimal("52.90"),
        Decimal("52.90"),
    )

    assert result == Decimal("52.90")


def test_preco_negativo_na_primeira_metade():
    with pytest.raises(ValueError):
        calculate_pizza_price(
            Decimal("-1.00"),
        )


def test_preco_negativo_na_segunda_metade():
    with pytest.raises(ValueError):
        calculate_pizza_price(
            Decimal("52.90"),
            Decimal("-1.00"),
        )

def test_pizza_com_borda():
    result = calculate_pizza_total(
        Decimal("65.90"),
        Decimal("9.90"),
    )

    assert result == Decimal("75.80")


def test_pizza_sem_borda():
    result = calculate_pizza_total(
        Decimal("52.90"),
    )

    assert result == Decimal("52.90")


def test_borda_com_preco_negativo():
    with pytest.raises(ValueError):
        calculate_pizza_total(
            Decimal("52.90"),
            Decimal("-1.00"),
        )

def test_taxa_entrega_mooca():
    result = calculate_delivery_fee(
        "DELIVERY",
        "Mooca",
    )

    assert result == Decimal("4.90")


def test_taxa_entrega_bras():
    result = calculate_delivery_fee(
        "DELIVERY",
        "Brás",
    )

    assert result == Decimal("6.90")


def test_retirada_na_loja():
    result = calculate_delivery_fee(
        "PICKUP",
    )

    assert result == Decimal("0.00")


def test_entrega_sem_bairro():
    with pytest.raises(ValueError):
        calculate_delivery_fee(
            "DELIVERY",
        )


def test_regiao_nao_atendida():
    with pytest.raises(ValueError):
        calculate_delivery_fee(
            "DELIVERY",
            "Santos",
        )


def test_metodo_de_recebimento_invalido():
    with pytest.raises(ValueError):
        calculate_delivery_fee(
            "MOTOBOY",
            "Mooca",
        )

def test_total_do_pedido_com_entrega():
    result = calculate_order_total(
        [
            Decimal("75.80"),
            Decimal("13.90"),
        ],
        Decimal("4.90"),
    )

    assert result == Decimal("94.60")


def test_total_do_pedido_sem_entrega():
    result = calculate_order_total(
        [
            Decimal("52.90"),
            Decimal("13.90"),
        ],
    )

    assert result == Decimal("66.80")


def test_pedido_sem_itens():
    result = calculate_order_total(
        [],
    )

    assert result == Decimal("0.00")


def test_item_com_valor_negativo():
    with pytest.raises(ValueError):
        calculate_order_total(
            [
                Decimal("-10.00"),
            ],
        )


def test_taxa_de_entrega_negativa():
    with pytest.raises(ValueError):
        calculate_order_total(
            [
                Decimal("50.00"),
            ],
            Decimal("-5.00"),
        )

def test_calculate_item_total():
    assert calculate_item_total(
        Decimal("52.90"),
        2,
    ) == Decimal("105.80")


def test_calculate_item_total_rejects_zero_quantity():
    with pytest.raises(ValueError, match="quantidade"):
        calculate_item_total(
            Decimal("52.90"),
            0,
        )


def test_calculate_item_total_rejects_negative_price():
    with pytest.raises(ValueError, match="preço unitário"):
        calculate_item_total(
            Decimal("-1.00"),
            1,
        )