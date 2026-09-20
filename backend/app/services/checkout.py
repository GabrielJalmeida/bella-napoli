from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.checkout import (
    validate_checkout_payment,
    validate_customer_data,
    validate_delivery_data,
    validate_order_has_items,
)
from app.domain.pricing import (
    calculate_item_total,
    calculate_pizza_price,
)
from app.domain.store_hours import (
    STORE_TIMEZONE,
    is_store_open,
)
from app.models.business_hours import BusinessHours
from app.models.customer import Customer
from app.models.delivery_zone import DeliveryZone
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_item_pizza_detail import OrderItemPizzaDetail
from app.models.order_item_pizza_flavor import OrderItemPizzaFlavor
from app.models.payment import Payment
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.crust import Crust
from app.models.crust_price import CrustPrice
from app.services.orders import recalculate_order_totals, transition_order_status
from app.services.payments import (
    confirm_pix_payment,
    create_payment_attempt,
    expire_pix_payment,
)


def _get_current_business_hours(
    session: Session,
    current_datetime: datetime,
) -> BusinessHours:
    local_datetime = current_datetime.astimezone(
        STORE_TIMEZONE
    )

    day_of_week = local_datetime.weekday()

    hours = session.scalar(
        select(BusinessHours).where(
            BusinessHours.day_of_week == day_of_week
        )
    )

    if hours is None:
        raise ValueError(
            "Horário de funcionamento não configurado."
        )

    return hours


def _validate_store_is_open(
    session: Session,
    current_datetime: datetime,
) -> None:
    hours = _get_current_business_hours(
        session,
        current_datetime,
    )

    if not is_store_open(
        current_datetime=current_datetime,
        is_closed=hours.is_closed,
        open_time=hours.open_time,
        close_time=hours.close_time,
    ):
        raise ValueError(
            "A Bella Napoli está fechada no momento."
        )


def _validate_order_items(
    session: Session,
    order: Order,
) -> list[OrderItem]:
    items = session.scalars(
        select(OrderItem)
        .where(OrderItem.order_id == order.id)
        .order_by(OrderItem.id)
    ).all()

    validate_order_has_items(len(items))

    for item in items:
        if item.quantity <= 0:
            raise ValueError(
                "O pedido possui item com quantidade inválida."
            )

        is_pizza = item.variant_name in {"P", "M", "G"}

        if not is_pizza:
            variant = session.scalar(
                select(ProductVariant)
                .join(
                    Product,
                    Product.id == ProductVariant.product_id,
                )
                .where(
                    ProductVariant.id == item.product_variant_id,
                    ProductVariant.active.is_(True),
                    Product.active.is_(True),
                )
            )

            if variant is None:
                raise ValueError(
                    "Um dos produtos do pedido não está mais disponível."
                )

            if variant.price != item.unit_price:
                raise ValueError(
                    f"O preço do item '{item.product_name}' mudou. "
                    "Revise o pedido antes de confirmar."
                )

            expected_total = calculate_item_total(
                item.unit_price,
                item.quantity,
            )

            if item.total_price != expected_total:
                raise ValueError(
                    "O total de um item do pedido está inconsistente."
                )

            continue

        flavors = session.scalars(
            select(OrderItemPizzaFlavor)
            .where(
                OrderItemPizzaFlavor.order_item_id == item.id
            )
            .order_by(OrderItemPizzaFlavor.slot)
        ).all()

        if len(flavors) not in {1, 2}:
            raise ValueError(
                "A configuração de uma pizza está inválida."
            )

        flavor_prices: list[Decimal] = []

        for flavor in flavors:
            variant = session.scalar(
                select(ProductVariant)
                .join(
                    Product,
                    Product.id == ProductVariant.product_id,
                )
                .where(
                    ProductVariant.product_id == flavor.flavor_id,
                    ProductVariant.name == item.variant_name,
                    ProductVariant.active.is_(True),
                    Product.active.is_(True),
                )
            )

            if variant is None:
                raise ValueError(
                    f"O sabor '{flavor.flavor_name}' "
                    "não está mais disponível nesse tamanho."
                )

            if flavor.slot == 1 and flavor.fraction == Decimal("1.0"):
                flavor_prices.append(variant.price)

            elif flavor.fraction == Decimal("0.5"):
                flavor_prices.append(variant.price)

            else:
                raise ValueError(
                    "A configuração das metades da pizza está inválida."
                )

        if len(flavor_prices) == 1:
            pizza_price = calculate_pizza_price(
                flavor_prices[0]
            )
        else:
            pizza_price = calculate_pizza_price(
                flavor_prices[0],
                flavor_prices[1],
            )

        detail = session.scalar(
            select(OrderItemPizzaDetail).where(
                OrderItemPizzaDetail.order_item_id == item.id
            )
        )

        crust_price = Decimal("0.00")

        if detail is not None:
            crust_price_record = session.scalar(
                select(CrustPrice)
                .join(
                    Crust,
                    Crust.id == CrustPrice.crust_id,
                )
                .where(
                    CrustPrice.crust_id == detail.crust_id,
                    CrustPrice.size == item.variant_name,
                    CrustPrice.active.is_(True),
                    Crust.active.is_(True),
                )
            )

            if crust_price_record is None:
                raise ValueError(
                    "A borda selecionada não está mais disponível."
                )

            crust_price = crust_price_record.price

            if crust_price != detail.crust_price:
                raise ValueError(
                    "O preço da borda mudou. "
                    "Revise o pedido antes de confirmar."
                )

        current_unit_price = (
            pizza_price + crust_price
        ).quantize(Decimal("0.01"))

        if current_unit_price != item.unit_price + (
            detail.crust_price if detail is not None
            else Decimal("0.00")
        ):
            raise ValueError(
                f"O preço da pizza '{item.product_name}' mudou. "
                "Revise o pedido antes de confirmar."
            )

        expected_total = calculate_item_total(
            current_unit_price,
            item.quantity,
        )

        if item.total_price != expected_total:
            raise ValueError(
                "O total de uma pizza do pedido está inconsistente."
            )

    return items


def _validate_delivery_zone(
    session: Session,
    order: Order,
) -> None:
    if order.delivery_method != "DELIVERY":
        return

    zone = session.scalar(
        select(DeliveryZone).where(
            DeliveryZone.neighborhood == order.delivery_neighborhood,
            DeliveryZone.active.is_(True),
        )
    )

    if zone is None:
        raise ValueError(
            "O bairro não é mais atendido para entrega."
        )

    if zone.fee != order.delivery_fee:
        raise ValueError(
            "A taxa de entrega mudou. "
            "Revise o pedido antes de confirmar."
        )


def finalize_order(
    session: Session,
    order_id: int,
    payment_method: str,
    change_for: Decimal | None = None,
    current_datetime: datetime | None = None,
) -> tuple[Order, Payment]:
    """
    Finaliza um pedido DRAFT.

    PIX:
        DRAFT → AWAITING_PAYMENT

    Outros métodos:
        DRAFT → CONFIRMED
    """

    order = session.get(Order, order_id)

    if order is None:
        raise ValueError("Pedido não encontrado.")

    if order.status != "DRAFT":
        raise ValueError(
            "Somente pedidos em DRAFT podem ser finalizados."
        )

    customer = None

    if order.customer_id is not None:
        customer = session.get(
            Customer,
            order.customer_id,
        )

    if customer is None:
        raise ValueError(
            "O pedido precisa possuir um cliente."
        )

    validate_customer_data(
        name=customer.name,
        phone=customer.phone,
    )

    _validate_order_items(
        session,
        order,
    )

    if order.delivery_method is None:
        raise ValueError(
            "É necessário escolher entrega ou retirada."
        )

    validate_delivery_data(
        delivery_method=order.delivery_method,
        delivery_neighborhood=order.delivery_neighborhood,
        delivery_zip_code=order.delivery_zip_code,
        delivery_street=order.delivery_street,
        delivery_number=order.delivery_number,
    )

    _validate_delivery_zone(
        session,
        order,
    )

    if current_datetime is None:
        current_datetime = datetime.now(timezone.utc)

    if current_datetime.tzinfo is None:
        raise ValueError(
            "A data e hora precisam possuir timezone."
        )

    _validate_store_is_open(
        session,
        current_datetime,
    )

    recalculate_order_totals(
        session,
        order,
    )

    validate_checkout_payment(
        payment_method=payment_method,
        order_total=order.total,
        change_for=change_for,
    )

    if payment_method == "PIX_DEMO":
        existing_payment = session.scalar(
            select(Payment)
            .where(
                Payment.order_id == order.id,
                Payment.method == "PIX_DEMO",
                Payment.status == "PENDING",
            )
            .order_by(Payment.id.desc())
        )

        if existing_payment is not None:
            now = datetime.now(timezone.utc)

            if (
                existing_payment.expires_at is not None
                and existing_payment.expires_at > now
            ):
                return order, existing_payment

            expire_pix_payment(
                session,
                existing_payment.id,
            )

    payment = create_payment_attempt(
        session=session,
        order_id=order.id,
        method=payment_method,
        change_for=change_for,
    )

    if payment_method == "PIX_DEMO":
        transition_order_status(
            session,
            order.id,
            "AWAITING_PAYMENT",
        )
    else:
        transition_order_status(
            session,
            order.id,
            "CONFIRMED",
        )

    session.flush()

    return order, payment

def confirm_order_pix_payment(
    session: Session,
    order_id: int,
    pix_token: str,
    current_datetime: datetime | None = None,
) -> tuple[Order, Payment]:
    """
    Confirma o pagamento PIX de um pedido.

    Fluxo normal:

        AWAITING_PAYMENT
            ↓
        Payment PENDING → PAID
            ↓
        Order → CONFIRMED

    PIX expirado:

        AWAITING_PAYMENT
            ↓
        Payment PENDING → EXPIRED
            ↓
        Order → PAYMENT_EXPIRED

    Operação idempotente:

        PAID → PAID
        CONFIRMED → CONFIRMED
    """

    if current_datetime is None:
        current_datetime = datetime.now(timezone.utc)

    if current_datetime.tzinfo is None:
        raise ValueError(
            "A data e hora precisam possuir timezone."
        )

    order = session.scalar(
        select(Order)
        .where(Order.id == order_id)
        .with_for_update()
    )

    if order is None:
        raise ValueError(
            "Pedido não encontrado."
        )

    payment = session.scalar(
        select(Payment)
        .where(
            Payment.order_id == order.id,
            Payment.pix_token == pix_token,
        )
        .with_for_update()
    )

    if payment is None:
        raise ValueError(
            "Pagamento PIX não encontrado para este pedido."
        )

    if payment.method != "PIX_DEMO":
        raise ValueError(
            "O pagamento informado não é PIX."
        )

    # Idempotência:
    # uma confirmação repetida não executa o fluxo novamente.
    if payment.status == "PAID":
        if order.status != "CONFIRMED":
            raise ValueError(
                "Pagamento já está pago, mas o pedido não está confirmado."
            )

        return order, payment

    if order.status != "AWAITING_PAYMENT":
        raise ValueError(
            "O pedido não está aguardando pagamento PIX."
        )

    if payment.status == "EXPIRED":
        transition_order_status(
            session,
            order.id,
            "PAYMENT_EXPIRED",
        )

        raise ValueError(
            "O pagamento PIX expirou."
        )

    if payment.status != "PENDING":
        raise ValueError(
            f"Pagamento não pode ser confirmado no status {payment.status}."
        )

    if payment.expires_at is None:
        raise ValueError(
            "Pagamento PIX sem data de expiração."
        )

    if current_datetime >= payment.expires_at:
        expire_pix_payment(
            session=session,
            payment_id=payment.id,
            current_datetime=current_datetime,
    )

        transition_order_status(
            session,
            order.id,
            "PAYMENT_EXPIRED",
        )

        raise ValueError(
            "O pagamento PIX expirou."
        )

    payment = confirm_pix_payment(
        session=session,
        pix_token=pix_token,
        current_datetime=current_datetime,
)

    transition_order_status(
        session,
        order.id,
        "CONFIRMED",
    )

    session.flush()

    return order, payment