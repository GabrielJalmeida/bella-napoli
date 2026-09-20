from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.pricing import (
    calculate_item_total,
    calculate_pizza_price,
    calculate_pizza_total,
)
from app.models.crust import Crust
from app.models.crust_price import CrustPrice
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_item_pizza_detail import OrderItemPizzaDetail
from app.models.order_item_pizza_flavor import OrderItemPizzaFlavor
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.services.orders import recalculate_order_totals


PIZZA_SIZES = {"P", "M", "G"}


def configure_pizza_item(
    session: Session,
    order_id: int,
    item_id: int,
    flavor_ids: list[int],
    crust_id: int | None = None,
) -> OrderItem:
    order = session.get(Order, order_id)

    if order is None:
        raise ValueError("Pedido não encontrado.")

    if order.status != "DRAFT":
        raise ValueError(
            "Só é possível configurar pizzas em pedidos DRAFT."
        )

    item = session.scalar(
        select(OrderItem).where(
            OrderItem.id == item_id,
            OrderItem.order_id == order_id,
        )
    )

    if item is None:
        raise ValueError("Item não encontrado neste pedido.")

    if item.variant_name not in PIZZA_SIZES:
        raise ValueError(
            "O tamanho informado não corresponde a uma pizza."
        )

    if len(flavor_ids) not in {1, 2}:
        raise ValueError(
            "Uma pizza deve possuir um ou dois sabores."
        )

    if any(flavor_id <= 0 for flavor_id in flavor_ids):
        raise ValueError("O sabor informado é inválido.")

    flavor_variants = session.scalars(
        select(ProductVariant)
        .join(Product, Product.id == ProductVariant.product_id)
        .where(
            ProductVariant.product_id.in_(flavor_ids),
            ProductVariant.name == item.variant_name,
            ProductVariant.active.is_(True),
            Product.active.is_(True),
        )
    ).all()

    variants_by_product_id = {
        variant.product_id: variant
        for variant in flavor_variants
    }

    products = session.scalars(
        select(Product).where(
            Product.id.in_(flavor_ids),
            Product.active.is_(True),
        )
    ).all()

    products_by_id = {
        product.id: product
        for product in products
    }

    if any(
        flavor_id not in variants_by_product_id
        or flavor_id not in products_by_id
        for flavor_id in flavor_ids
    ):
        raise ValueError(
            "Um dos sabores não possui uma variante ativa "
            "para este tamanho."
        )

    first_variant = variants_by_product_id[flavor_ids[0]]
    first_product = products_by_id[flavor_ids[0]]

    second_variant = None
    second_product = None

    if len(flavor_ids) == 2:
        second_variant = variants_by_product_id[flavor_ids[1]]
        second_product = products_by_id[flavor_ids[1]]

    pizza_price = calculate_pizza_price(
        first_variant.price,
        second_variant.price if second_variant is not None else None,
    )

    crust_price = Decimal("0.00")
    crust = None

    if crust_id is not None:
        crust_result = session.execute(
            select(CrustPrice, Crust)
            .join(Crust, Crust.id == CrustPrice.crust_id)
            .where(
                CrustPrice.crust_id == crust_id,
                CrustPrice.size == item.variant_name,
                CrustPrice.active.is_(True),
                Crust.active.is_(True),
            )
        ).first()

        if crust_result is None:
            raise ValueError(
                "A borda informada não está disponível "
                "para este tamanho."
            )

        crust_price_record, crust = crust_result
        crust_price = crust_price_record.price

    existing_flavors = session.scalars(
        select(OrderItemPizzaFlavor).where(
            OrderItemPizzaFlavor.order_item_id == item.id,
        )
    ).all()

    for existing_flavor in existing_flavors:
        session.delete(existing_flavor)

    existing_detail = session.scalar(
        select(OrderItemPizzaDetail).where(
            OrderItemPizzaDetail.order_item_id == item.id,
        )
    )

    if existing_detail is not None:
        session.delete(existing_detail)

    session.flush()

    if len(flavor_ids) == 1:
        item.product_name = first_product.name
        fraction_values = [Decimal("1.0")]
    else:
        item.product_name = "Pizza meio a meio"
        fraction_values = [
            Decimal("0.5"),
            Decimal("0.5"),
        ]

    item.product_variant_id = first_variant.id
    item.unit_price = pizza_price

    for slot, flavor_id, fraction in zip(
        range(1, len(flavor_ids) + 1),
        flavor_ids,
        fraction_values,
    ):
        product = products_by_id[flavor_id]

        session.add(
            OrderItemPizzaFlavor(
                order_item_id=item.id,
                flavor_id=flavor_id,
                flavor_name=product.name,
                slot=slot,
                fraction=fraction,
            )
        )

    if crust is not None:
        session.add(
            OrderItemPizzaDetail(
                order_item_id=item.id,
                crust_id=crust.id,
                crust_name=crust.name,
                crust_price=crust_price,
            )
        )

    unit_price_with_crust = calculate_pizza_total(
        pizza_price,
        crust_price,
    )

    item.total_price = calculate_item_total(
        unit_price_with_crust,
        item.quantity,
    )

    session.flush()

    recalculate_order_totals(session, order)

    return item