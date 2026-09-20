from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import engine
from app.domain.checkout import (
    validate_checkout_payment,
    validate_customer_data,
    validate_delivery_data,
    validate_delivery_method,
    validate_order_has_items,
)
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.services.checkout import (
    confirm_order_pix_payment,
    finalize_order,
)
from app.services.orders import (
    create_draft_order,
    recalculate_order_totals,
    set_order_delivery,
)

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


@pytest.fixture
def session():
    session = Session(engine)

    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_finalize_order_with_credit_confirms_order(session: Session):
    order = create_draft_order(session)

    customer = Customer(
        name="Gabriel Almeida",
        phone="11999999999",
    )

    session.add(customer)
    session.flush()

    order.customer_id = customer.id

    variant = session.scalar(
        select(ProductVariant)
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .where(
            Product.name == "Coca-Cola 2L",
            ProductVariant.name == "2L",
            Product.active.is_(True),
            ProductVariant.active.is_(True),
        )
    )

    if variant is None:
        variant = session.scalar(
            select(ProductVariant)
            .join(
                Product,
                Product.id == ProductVariant.product_id,
            )
            .where(
                Product.active.is_(True),
                ProductVariant.active.is_(True),
                ProductVariant.name == "2L",
            )
            .order_by(ProductVariant.id)
        )

    assert variant is not None

    product = session.get(
        Product,
        variant.product_id,
    )

    assert product is not None

    item = OrderItem(
        order_id=order.id,
        product_variant_id=variant.id,
        product_name=product.name,
        variant_name=variant.name,
        unit_price=variant.price,
        quantity=1,
        total_price=variant.price,
    )

    session.add(item)
    session.flush()

    order.delivery_method = "PICKUP"
    order.delivery_fee = Decimal("0.00")

    confirmed_order, payment = finalize_order(
        session=session,
        order_id=order.id,
        payment_method="CREDIT_ON_DELIVERY",
        current_datetime=datetime(
            2026,
            9,
            22,
            19,
            0,
            tzinfo=BRAZIL_TZ,
        ),
    )

    assert confirmed_order.status == "CONFIRMED"
    assert payment.method == "CREDIT_ON_DELIVERY"
    assert payment.status == "PENDING"
    assert payment.amount == variant.price


def test_validate_delivery_method_accepts_delivery():
    validate_delivery_method("DELIVERY")


def test_validate_delivery_method_accepts_pickup():
    validate_delivery_method("PICKUP")


def test_validate_delivery_method_rejects_invalid_method():
    with pytest.raises(
        ValueError,
        match="Método de entrega inválido",
    ):
        validate_delivery_method("INVALID")


def test_delivery_requires_address():
    validate_delivery_data(
        delivery_method="DELIVERY",
        delivery_neighborhood="Mooca",
        delivery_zip_code="03123000",
        delivery_street="Rua Bella Napoli",
        delivery_number="214",
    )


def test_delivery_rejects_missing_street():
    with pytest.raises(
        ValueError,
        match="rua",
    ):
        validate_delivery_data(
            delivery_method="DELIVERY",
            delivery_neighborhood="Mooca",
            delivery_zip_code="03123000",
            delivery_street="",
            delivery_number="214",
        )


def test_pickup_rejects_delivery_address():
    with pytest.raises(
        ValueError,
        match="retirada",
    ):
        validate_delivery_data(
            delivery_method="PICKUP",
            delivery_neighborhood="Mooca",
            delivery_zip_code=None,
            delivery_street=None,
            delivery_number=None,
        )


def test_pickup_without_address_is_valid():
    validate_delivery_data(
        delivery_method="PICKUP",
        delivery_neighborhood=None,
        delivery_zip_code=None,
        delivery_street=None,
        delivery_number=None,
    )


def test_cash_without_change_is_valid():
    validate_checkout_payment(
        payment_method="CASH",
        order_total=Decimal("57.80"),
        change_for=None,
    )


def test_cash_with_higher_change_value_is_valid():
    validate_checkout_payment(
        payment_method="CASH",
        order_total=Decimal("57.80"),
        change_for=Decimal("100.00"),
    )


def test_cash_rejects_change_equal_to_total():
    with pytest.raises(
        ValueError,
        match="troco",
    ):
        validate_checkout_payment(
            payment_method="CASH",
            order_total=Decimal("57.80"),
            change_for=Decimal("57.80"),
        )


def test_non_cash_rejects_change():
    with pytest.raises(
        ValueError,
        match="Troco",
    ):
        validate_checkout_payment(
            payment_method="PIX_DEMO",
            order_total=Decimal("57.80"),
            change_for=Decimal("100.00"),
        )


def test_zero_total_is_rejected():
    with pytest.raises(
        ValueError,
        match="maior que zero",
    ):
        validate_checkout_payment(
            payment_method="CASH",
            order_total=Decimal("0.00"),
        )


def test_customer_requires_name():
    with pytest.raises(
        ValueError,
        match="nome",
    ):
        validate_customer_data(
            name="",
            phone="11999999999",
        )


def test_customer_requires_phone():
    with pytest.raises(
        ValueError,
        match="telefone",
    ):
        validate_customer_data(
            name="Gabriel Almeida",
            phone="",
        )


def test_order_requires_items():
    with pytest.raises(
        ValueError,
        match="sem itens",
    ):
        validate_order_has_items(0)


def test_order_with_items_is_valid():
    validate_order_has_items(1)

def create_checkout_order(
    session: Session,
    delivery_method: str = "PICKUP",
    neighborhood: str | None = None,
) -> Order:
    order = create_draft_order(session)

    customer = Customer(
        name="Cliente Teste",
        phone="11988887777",
    )

    session.add(customer)
    session.flush()

    order.customer_id = customer.id

    variants = session.scalars(
        select(ProductVariant)
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .where(
            Product.active.is_(True),
            ProductVariant.active.is_(True),
        )
        .order_by(ProductVariant.id)
    ).all()

    variant = next(
        (
            item
            for item in variants
            if item.name not in {"P", "M", "G"}
        ),
        None,
    )

    assert variant is not None

    product = session.get(
        Product,
        variant.product_id,
    )

    assert product is not None

    item = OrderItem(
        order_id=order.id,
        product_variant_id=variant.id,
        product_name=product.name,
        variant_name=variant.name,
        unit_price=variant.price,
        quantity=1,
        total_price=variant.price,
    )

    session.add(item)
    session.flush()

    if delivery_method == "PICKUP":
        set_order_delivery(
            session=session,
            order_id=order.id,
            delivery_method="PICKUP",
        )

    else:
        assert neighborhood is not None

        set_order_delivery(
            session=session,
            order_id=order.id,
            delivery_method="DELIVERY",
            neighborhood=neighborhood,
        )

        order.delivery_zip_code = "03123000"
        order.delivery_street = "Rua Bella Napoli"
        order.delivery_number = "214"
        order.delivery_complement = None
        order.delivery_reference = "Próximo à praça"

        session.flush()

    recalculate_order_totals(
        session,
        order,
    )

    return order


def test_finalize_order_with_delivery_confirms_order(session: Session):
    order = create_checkout_order(
        session,
        delivery_method="DELIVERY",
        neighborhood="Mooca",
    )

    confirmed_order, payment = finalize_order(
        session=session,
        order_id=order.id,
        payment_method="CREDIT_ON_DELIVERY",
        current_datetime=datetime(
            2026,
            9,
            22,
            19,
            0,
            tzinfo=BRAZIL_TZ,
        ),
    )

    assert confirmed_order.status == "CONFIRMED"
    assert confirmed_order.delivery_method == "DELIVERY"
    assert confirmed_order.delivery_neighborhood == "Mooca"
    assert confirmed_order.delivery_fee == Decimal("4.90")

    assert payment.method == "CREDIT_ON_DELIVERY"
    assert payment.status == "PENDING"
    assert payment.amount == confirmed_order.total


def test_finalize_order_with_cash_and_change_confirms_order(
    session: Session,
):
    order = create_checkout_order(
        session,
        delivery_method="PICKUP",
    )

    change_for = order.total + Decimal("10.00")

    confirmed_order, payment = finalize_order(
        session=session,
        order_id=order.id,
        payment_method="CASH",
        change_for=change_for,
        current_datetime=datetime(
            2026,
            9,
            22,
            19,
            0,
            tzinfo=BRAZIL_TZ,
        ),
    )

    assert confirmed_order.status == "CONFIRMED"
    assert payment.method == "CASH"
    assert payment.status == "PENDING"
    assert payment.amount == confirmed_order.total
    assert payment.change_for == change_for


def test_finalize_order_rejects_invalid_cash_change(
    session: Session,
):
    order = create_checkout_order(
        session,
        delivery_method="PICKUP",
    )

    with pytest.raises(
        ValueError,
        match="troco",
    ):
        finalize_order(
            session=session,
            order_id=order.id,
            payment_method="CASH",
            change_for=order.total,
            current_datetime=datetime(
                2026,
                9,
                22,
                19,
                0,
                tzinfo=BRAZIL_TZ,
            ),
        )


def test_finalize_order_rejects_closed_store(
    session: Session,
):
    order = create_checkout_order(
        session,
        delivery_method="PICKUP",
    )

    with pytest.raises(
        ValueError,
        match="fechada",
    ):
        finalize_order(
            session=session,
            order_id=order.id,
            payment_method="CREDIT_ON_DELIVERY",
            current_datetime=datetime(
                2026,
                9,
                21,
                20,
                0,
                tzinfo=BRAZIL_TZ,
            ),
        )

    assert order.status == "DRAFT"


def test_finalize_order_rejects_unsupported_delivery_zone(
    session: Session,
):
    order = create_checkout_order(
        session,
        delivery_method="PICKUP",
    )

    order.delivery_method = "DELIVERY"
    order.delivery_neighborhood = "Bairro Inexistente"
    order.delivery_fee = Decimal("0.00")
    order.delivery_zip_code = "03123000"
    order.delivery_street = "Rua Bella Napoli"
    order.delivery_number = "214"

    session.flush()

    with pytest.raises(
        ValueError,
        match="atendido",
    ):
        finalize_order(
            session=session,
            order_id=order.id,
            payment_method="CREDIT_ON_DELIVERY",
            current_datetime=datetime(
                2026,
                9,
                22,
                19,
                0,
                tzinfo=BRAZIL_TZ,
            ),
        )

    assert order.status == "DRAFT"

def test_pix_payment_confirms_order(
    session: Session,
):
    order = create_checkout_order(
        session,
        delivery_method="PICKUP",
    )

    pending_order, payment = finalize_order(
        session=session,
        order_id=order.id,
        payment_method="PIX_DEMO",
        current_datetime=datetime(
            2026,
            9,
            22,
            19,
            0,
            tzinfo=BRAZIL_TZ,
        ),
    )

    assert pending_order.status == "AWAITING_PAYMENT"
    assert payment.status == "PENDING"

    confirmed_order, confirmed_payment = (
        confirm_order_pix_payment(
            session=session,
            order_id=order.id,
            pix_token=payment.pix_token,
        )
    )

    assert confirmed_order.status == "CONFIRMED"
    assert confirmed_payment.status == "PAID"
    assert confirmed_payment.paid_at is not None


def test_pix_payment_confirmation_is_idempotent(
    session: Session,
):
    order = create_checkout_order(
        session,
        delivery_method="PICKUP",
    )

    _, payment = finalize_order(
        session=session,
        order_id=order.id,
        payment_method="PIX_DEMO",
        current_datetime=datetime(
            2026,
            9,
            22,
            19,
            0,
            tzinfo=BRAZIL_TZ,
        ),
    )

    first_order, first_payment = confirm_order_pix_payment(
        session=session,
        order_id=order.id,
        pix_token=payment.pix_token,
    )

    first_paid_at = first_payment.paid_at

    second_order, second_payment = (
        confirm_order_pix_payment(
            session=session,
            order_id=order.id,
            pix_token=payment.pix_token,
        )
    )

    assert first_order.id == second_order.id
    assert first_payment.id == second_payment.id
    assert second_order.status == "CONFIRMED"
    assert second_payment.status == "PAID"
    assert second_payment.paid_at == first_paid_at


def test_expired_pix_changes_order_to_payment_expired(
    session: Session,
):
    order = create_checkout_order(
        session,
        delivery_method="PICKUP",
    )

    _, payment = finalize_order(
        session=session,
        order_id=order.id,
        payment_method="PIX_DEMO",
        current_datetime=datetime(
            2026,
            9,
            22,
            19,
            0,
            tzinfo=BRAZIL_TZ,
        ),
    )

    payment.expires_at = datetime(
        2026,
        9,
        22,
        18,
        59,
        tzinfo=BRAZIL_TZ,
    )

    session.flush()

    with pytest.raises(
        ValueError,
        match="expirou",
):
        confirm_order_pix_payment(
            session=session,
            order_id=order.id,
            pix_token=payment.pix_token,
            current_datetime=datetime(
                2026,
                9,
                22,
                19,
                0,
                tzinfo=BRAZIL_TZ,
            ),
        )

    session.refresh(order)
    session.refresh(payment)

    assert order.status == "PAYMENT_EXPIRED"
    assert payment.status == "EXPIRED"


def test_pix_token_cannot_confirm_another_order(
    session: Session,
):
    first_order = create_checkout_order(
        session,
        delivery_method="PICKUP",
    )

    second_order = create_checkout_order(
        session,
        delivery_method="PICKUP",
    )

    _, first_payment = finalize_order(
        session=session,
        order_id=first_order.id,
        payment_method="PIX_DEMO",
        current_datetime=datetime(
            2026,
            9,
            22,
            19,
            0,
            tzinfo=BRAZIL_TZ,
        ),
    )

    _, second_payment = finalize_order(
        session=session,
        order_id=second_order.id,
        payment_method="PIX_DEMO",
        current_datetime=datetime(
            2026,
            9,
            22,
            19,
            0,
            tzinfo=BRAZIL_TZ,
        ),
    )

    with pytest.raises(
        ValueError,
        match="não encontrado",
    ):
        confirm_order_pix_payment(
            session=session,
            order_id=first_order.id,
            pix_token=second_payment.pix_token,
        )

    assert first_order.status == "AWAITING_PAYMENT"
    assert first_payment.status == "PENDING"
    assert second_payment.status == "PENDING"