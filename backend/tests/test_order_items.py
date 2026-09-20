from decimal import Decimal
from app.models.order_item import OrderItem
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.services.order_items import (
    add_item_to_draft_order,
    remove_order_item,
    update_order_item_quantity,
)
from app.services.orders import (
    create_draft_order,
    set_order_delivery,
)

from app.services.pizza_items import configure_pizza_item
from app.models.order_item_pizza_flavor import OrderItemPizzaFlavor

from app.models.crust import Crust
from app.models.order_item_pizza_detail import OrderItemPizzaDetail

@pytest.fixture
def session():
    session = Session(engine)

    try:
        yield session
    finally:
        session.rollback()
        session.close()


def get_variant(
    session: Session,
    product_name: str,
    variant_name: str,
) -> ProductVariant:
    stmt = (
        select(ProductVariant)
        .join(Product, Product.id == ProductVariant.product_id)
        .where(
            Product.name == product_name,
            ProductVariant.name == variant_name,
        )
    )

    variant = session.scalar(stmt)

    assert variant is not None

    return variant


def test_add_item_to_draft_order_creates_snapshot(session: Session):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=2,
    )

    assert item.order_id == order.id
    assert item.product_variant_id == variant.id

    assert item.product_name == "Margherita"
    assert item.variant_name == "G"

    assert item.unit_price == Decimal("52.90")
    assert item.quantity == 2
    assert item.total_price == Decimal("105.80")

    assert order.subtotal == Decimal("105.80")
    assert order.total == Decimal("105.80")


def test_add_item_rejects_non_draft_order(session: Session):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    order.status = "CONFIRMED"
    session.flush()

    with pytest.raises(
        ValueError,
        match="DRAFT",
    ):
        add_item_to_draft_order(
            session,
            order_id=order.id,
            product_variant_id=variant.id,
            quantity=1,
        )


def test_add_item_rejects_inactive_variant(session: Session):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    variant.active = False
    session.flush()

    with pytest.raises(
        ValueError,
        match="disponível",
    ):
        add_item_to_draft_order(
            session,
            order_id=order.id,
            product_variant_id=variant.id,
            quantity=1,
        )


def test_add_item_rejects_invalid_quantity(session: Session):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    with pytest.raises(
        ValueError,
        match="quantidade",
    ):
        add_item_to_draft_order(
            session,
            order_id=order.id,
            product_variant_id=variant.id,
            quantity=0,
        )

def test_add_multiple_items_recalculates_order_totals(session: Session):
    order = create_draft_order(session)

    margherita = get_variant(session, "Margherita", "G")
    calabresa = get_variant(session, "Calabresa", "G")

    add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=margherita.id,
        quantity=1,
    )

    add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=calabresa.id,
        quantity=1,
    )

    assert order.subtotal == Decimal("107.80")
    assert order.total == Decimal("107.80")

def test_update_order_item_quantity_recalculates_totals(
    session: Session,
):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=1,
    )

    updated_item = update_order_item_quantity(
        session,
        order_id=order.id,
        item_id=item.id,
        quantity=3,
    )

    assert updated_item.quantity == 3
    assert updated_item.unit_price == Decimal("52.90")
    assert updated_item.total_price == Decimal("158.70")

    assert order.subtotal == Decimal("158.70")
    assert order.total == Decimal("158.70")


def test_update_order_item_rejects_zero_quantity(
    session: Session,
):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=1,
    )

    with pytest.raises(
        ValueError,
        match="quantidade",
    ):
        update_order_item_quantity(
            session,
            order_id=order.id,
            item_id=item.id,
            quantity=0,
        )


def test_update_order_item_rejects_non_draft_order(
    session: Session,
):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=1,
    )

    order.status = "CONFIRMED"
    session.flush()

    with pytest.raises(
        ValueError,
        match="DRAFT",
    ):
        update_order_item_quantity(
            session,
            order_id=order.id,
            item_id=item.id,
            quantity=2,
        )


def test_update_order_item_rejects_item_from_another_order(
    session: Session,
):
    order_a = create_draft_order(session)
    order_b = create_draft_order(session)

    variant = get_variant(session, "Margherita", "G")

    item_b = add_item_to_draft_order(
        session,
        order_id=order_b.id,
        product_variant_id=variant.id,
        quantity=1,
    )

    with pytest.raises(
        ValueError,
        match="não encontrado",
    ):
        update_order_item_quantity(
            session,
            order_id=order_a.id,
            item_id=item_b.id,
            quantity=2,
        )

def test_remove_order_item_recalculates_totals(
    session: Session,
):
    order = create_draft_order(session)

    margherita = get_variant(session, "Margherita", "G")
    calabresa = get_variant(session, "Calabresa", "G")

    margherita_item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=margherita.id,
        quantity=1,
    )

    calabresa_item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=calabresa.id,
        quantity=1,
    )

    assert order.subtotal == Decimal("107.80")

    remove_order_item(
        session,
        order_id=order.id,
        item_id=calabresa_item.id,
    )

    assert session.get(OrderItem, calabresa_item.id) is None

    assert session.get(OrderItem, margherita_item.id) is not None

    assert order.subtotal == Decimal("52.90")
    assert order.total == Decimal("52.90")


def test_remove_order_item_rejects_non_draft_order(
    session: Session,
):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=1,
    )

    order.status = "CONFIRMED"
    session.flush()

    with pytest.raises(
        ValueError,
        match="DRAFT",
    ):
        remove_order_item(
            session,
            order_id=order.id,
            item_id=item.id,
        )


def test_remove_order_item_rejects_item_from_another_order(
    session: Session,
):
    order_a = create_draft_order(session)
    order_b = create_draft_order(session)

    variant = get_variant(session, "Margherita", "G")

    item_b = add_item_to_draft_order(
        session,
        order_id=order_b.id,
        product_variant_id=variant.id,
        quantity=1,
    )

    with pytest.raises(
        ValueError,
        match="não encontrado",
    ):
        remove_order_item(
            session,
            order_id=order_a.id,
            item_id=item_b.id,
        )

def test_item_plus_delivery_recalculates_order_total(
    session: Session,
):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=1,
    )

    set_order_delivery(
        session,
        order_id=order.id,
        delivery_method="DELIVERY",
        neighborhood="Mooca",
    )

    assert order.subtotal == Decimal("52.90")
    assert order.delivery_fee == Decimal("4.90")
    assert order.total == Decimal("57.80")
    assert order.delivery_method == "DELIVERY"
    assert order.delivery_neighborhood == "Mooca"


def test_change_delivery_region_updates_fee(
    session: Session,
):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=1,
    )

    set_order_delivery(
        session,
        order_id=order.id,
        delivery_method="DELIVERY",
        neighborhood="Mooca",
    )

    assert order.delivery_fee == Decimal("4.90")
    assert order.total == Decimal("57.80")

    set_order_delivery(
        session,
        order_id=order.id,
        delivery_method="DELIVERY",
        neighborhood="Tatuapé",
    )

    assert order.delivery_neighborhood == "Tatuapé"
    assert order.delivery_fee == Decimal("7.90")
    assert order.total == Decimal("60.80")


def test_change_delivery_to_pickup_removes_fee(
    session: Session,
):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=1,
    )

    set_order_delivery(
        session,
        order_id=order.id,
        delivery_method="DELIVERY",
        neighborhood="Mooca",
    )

    set_order_delivery(
        session,
        order_id=order.id,
        delivery_method="PICKUP",
    )

    assert order.delivery_method == "PICKUP"
    assert order.delivery_neighborhood is None
    assert order.delivery_fee == Decimal("0.00")
    assert order.total == Decimal("52.90")

def test_configure_whole_pizza(
    session: Session,
):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=1,
    )

    configure_pizza_item(
        session,
        order_id=order.id,
        item_id=item.id,
        flavor_ids=[variant.product_id],
    )

    assert item.product_name == "Margherita"
    assert item.variant_name == "G"
    assert item.unit_price == Decimal("52.90")
    assert item.total_price == Decimal("52.90")

    flavors = session.scalars(
        select(OrderItemPizzaFlavor).where(
            OrderItemPizzaFlavor.order_item_id == item.id
        )
    ).all()

    assert len(flavors) == 1
    assert flavors[0].flavor_name == "Margherita"
    assert flavors[0].slot == 1
    assert flavors[0].fraction == Decimal("1.0")

def test_configure_half_and_half_pizza(
    session: Session,
):
    order = create_draft_order(session)

    margherita = get_variant(session, "Margherita", "G")
    calabresa = get_variant(session, "Calabresa", "G")

    item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=margherita.id,
        quantity=1,
    )

    configure_pizza_item(
        session,
        order_id=order.id,
        item_id=item.id,
        flavor_ids=[
            margherita.product_id,
            calabresa.product_id,
        ],
    )

    assert item.product_name == "Pizza meio a meio"
    assert item.unit_price == Decimal("53.90")
    assert item.total_price == Decimal("53.90")

    flavors = session.scalars(
        select(OrderItemPizzaFlavor)
        .where(
            OrderItemPizzaFlavor.order_item_id == item.id
        )
        .order_by(OrderItemPizzaFlavor.slot)
    ).all()

    assert len(flavors) == 2

    assert flavors[0].flavor_name == "Margherita"
    assert flavors[0].slot == 1
    assert flavors[0].fraction == Decimal("0.5")

    assert flavors[1].flavor_name == "Calabresa"
    assert flavors[1].slot == 2
    assert flavors[1].fraction == Decimal("0.5")

def test_configure_half_and_half_allows_same_flavor(
    session: Session,
):
    order = create_draft_order(session)
    calabresa = get_variant(session, "Calabresa", "G")

    item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=calabresa.id,
        quantity=1,
    )

    configure_pizza_item(
        session,
        order_id=order.id,
        item_id=item.id,
        flavor_ids=[
            calabresa.product_id,
            calabresa.product_id,
        ],
    )

    assert item.unit_price == Decimal("54.90")
    assert item.total_price == Decimal("54.90")

    flavors = session.scalars(
        select(OrderItemPizzaFlavor)
        .where(
            OrderItemPizzaFlavor.order_item_id == item.id
        )
        .order_by(OrderItemPizzaFlavor.slot)
    ).all()

    assert len(flavors) == 2
    assert flavors[0].flavor_id == calabresa.product_id
    assert flavors[1].flavor_id == calabresa.product_id

def test_configure_pizza_with_crust(
    session: Session,
):
    order = create_draft_order(session)

    margherita = get_variant(session, "Margherita", "G")

    item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=margherita.id,
        quantity=1,
    )

    crust = session.scalar(
        select(Crust).where(
            Crust.name == "Catupiry"
        )
    )

    assert crust is not None

    configure_pizza_item(
        session,
        order_id=order.id,
        item_id=item.id,
        flavor_ids=[margherita.product_id],
        crust_id=crust.id,
    )

    assert item.unit_price == Decimal("52.90")
    assert item.total_price == Decimal("62.80")

    detail = session.scalar(
        select(OrderItemPizzaDetail).where(
            OrderItemPizzaDetail.order_item_id == item.id
        )
    )

    assert detail is not None
    assert detail.crust_name == "Catupiry"
    assert detail.crust_price == Decimal("9.90")

def test_configure_pizza_rejects_two_invalid_flavors(
    session: Session,
):
    order = create_draft_order(session)
    variant = get_variant(session, "Margherita", "G")

    item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=1,
    )

    with pytest.raises(
        ValueError,
        match="um ou dois sabores",
    ):
        configure_pizza_item(
            session,
            order_id=order.id,
            item_id=item.id,
            flavor_ids=[
                1,
                2,
                3,
            ],
        )


def test_configure_pizza_rejects_non_pizza_size(
    session: Session,
):
    drink = get_variant(
        session,
        "Coca-Cola",
        "2L",
    )

    order = create_draft_order(session)

    item = add_item_to_draft_order(
        session,
        order_id=order.id,
        product_variant_id=drink.id,
        quantity=1,
    )

    with pytest.raises(
        ValueError,
        match="não corresponde a uma pizza",
    ):
        configure_pizza_item(
            session,
            order_id=order.id,
            item_id=item.id,
            flavor_ids=[drink.product_id],
        )