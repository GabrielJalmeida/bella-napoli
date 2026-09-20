from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.pricing import calculate_item_total
from app.models.order import Order
from app.services.orders import recalculate_order_totals
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant


def add_item_to_draft_order(
    session: Session,
    order_id: int,
    product_variant_id: int,
    quantity: int,
) -> OrderItem:
    order = session.get(Order, order_id)

    if order is None:
        raise ValueError("Pedido não encontrado.")

    if order.status != "DRAFT":
        raise ValueError("Só é possível adicionar itens a pedidos em DRAFT.")

    stmt = (
        select(ProductVariant, Product)
        .join(Product, Product.id == ProductVariant.product_id)
        .where(
            ProductVariant.id == product_variant_id,
            ProductVariant.active.is_(True),
            Product.active.is_(True),
        )
    )

    result = session.execute(stmt).first()

    if result is None:
        raise ValueError("A variante informada não está disponível.")

    product_variant, product = result

    total_price = calculate_item_total(
        product_variant.price,
        quantity,
    )

    item = OrderItem(
        order_id=order.id,
        product_variant_id=product_variant.id,
        product_name=product.name,
        variant_name=product_variant.name,
        unit_price=product_variant.price,
        quantity=quantity,
        total_price=total_price,
    )

    session.add(item)
    session.flush()

    recalculate_order_totals(session, order)

    return item

def update_order_item_quantity(
    session: Session,
    order_id: int,
    item_id: int,
    quantity: int,
) -> OrderItem:
    order = session.get(Order, order_id)

    if order is None:
        raise ValueError("Pedido não encontrado.")

    if order.status != "DRAFT":
        raise ValueError("Só é possível alterar itens de pedidos em DRAFT.")

    if quantity <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    item = session.scalar(
        select(OrderItem).where(
            OrderItem.id == item_id,
            OrderItem.order_id == order_id,
        )
    )

    if item is None:
        raise ValueError("Item não encontrado neste pedido.")

    item.quantity = quantity
    item.total_price = calculate_item_total(
        item.unit_price,
        quantity,
    )

    session.flush()

    recalculate_order_totals(session, order)

    return item

def remove_order_item(
    session: Session,
    order_id: int,
    item_id: int,
) -> None:
    order = session.get(Order, order_id)

    if order is None:
        raise ValueError("Pedido não encontrado.")

    if order.status != "DRAFT":
        raise ValueError("Só é possível remover itens de pedidos em DRAFT.")

    item = session.scalar(
        select(OrderItem).where(
            OrderItem.id == item_id,
            OrderItem.order_id == order_id,
        )
    )

    if item is None:
        raise ValueError("Item não encontrado neste pedido.")

    session.delete(item)
    session.flush()

    recalculate_order_totals(session, order)