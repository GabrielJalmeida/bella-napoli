import secrets
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.order_status import validate_order_status_transition
from app.domain.pricing import calculate_delivery_fee
from app.models.customer import Customer
from app.models.customer_address import CustomerAddress
from app.models.delivery_zone import DeliveryZone
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory


ORDER_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ORDER_CODE_LENGTH = 8


def generate_order_code() -> str:
    """
    Gera um código curto e legível para identificar publicamente um pedido.
    """

    random_part = "".join(
        secrets.choice(ORDER_CODE_ALPHABET)
        for _ in range(ORDER_CODE_LENGTH)
    )

    return f"BN-{random_part}"


def create_draft_order(session: Session) -> Order:
    """
    Cria um novo pedido no estado DRAFT.

    A função adiciona o pedido à sessão e executa flush,
    mas não faz commit. A transação fica sob responsabilidade
    de quem chamou o serviço.
    """

    for _ in range(5):
        code = generate_order_code()

        existing_order = session.scalar(
            select(Order).where(Order.code == code)
        )

        if existing_order is not None:
            continue

        order = Order(
            code=code,
            status="DRAFT",
            subtotal=Decimal("0.00"),
            delivery_fee=Decimal("0.00"),
            total=Decimal("0.00"),
            delivery_method=None,
            delivery_neighborhood=None,
            customer_id=None,
        )

        session.add(order)
        session.flush()

        history = OrderStatusHistory(
            order_id=order.id,
            from_status=None,
            to_status="DRAFT",
        )

        session.add(history)
        session.flush()

        return order

    raise RuntimeError(
        "Não foi possível gerar um código único para o pedido."
    )


def recalculate_order_totals(
    session: Session,
    order: Order,
) -> None:
    subtotal = session.scalar(
        select(
            func.coalesce(
                func.sum(OrderItem.total_price),
                Decimal("0.00"),
            )
        ).where(
            OrderItem.order_id == order.id
        )
    )

    order.subtotal = subtotal
    order.total = subtotal + order.delivery_fee


def _get_delivery_zone_fee(
    session: Session,
    neighborhood: str,
) -> Decimal:
    neighborhood = neighborhood.strip()

    zone = session.scalar(
        select(DeliveryZone).where(
            DeliveryZone.neighborhood == neighborhood,
            DeliveryZone.active.is_(True),
        )
    )

    if zone is None:
        raise ValueError(
            "Bairro não é uma área atendida para entrega."
        )

    return zone.fee


def set_order_delivery(
    session: Session,
    order_id: int,
    delivery_method: str,
    neighborhood: str | None = None,
) -> Order:
    order = session.get(Order, order_id)

    if order is None:
        raise ValueError("Pedido não encontrado.")

    if order.status != "DRAFT":
        raise ValueError(
            "Só é possível alterar a entrega de pedidos em DRAFT."
        )

    if delivery_method == "PICKUP":
        if neighborhood is not None:
            raise ValueError("Retirada não deve informar bairro.")

        delivery_fee = calculate_delivery_fee(
            delivery_method="PICKUP",
        )

        order.delivery_method = "PICKUP"
        order.delivery_fee = delivery_fee

        order.delivery_zip_code = None
        order.delivery_street = None
        order.delivery_number = None
        order.delivery_complement = None
        order.delivery_neighborhood = None
        order.delivery_reference = None

    elif delivery_method == "DELIVERY":
        if not neighborhood or not neighborhood.strip():
            raise ValueError(
                "O bairro é obrigatório para entrega."
            )

        neighborhood = neighborhood.strip()

        delivery_fee = _get_delivery_zone_fee(
            session,
            neighborhood,
        )

        delivery_fee = calculate_delivery_fee(
            delivery_method="DELIVERY",
            delivery_fee=delivery_fee,
        )

        order.delivery_method = "DELIVERY"
        order.delivery_neighborhood = neighborhood
        order.delivery_fee = delivery_fee

    else:
        raise ValueError("Método de entrega inválido.")

    recalculate_order_totals(session, order)

    return order


def set_order_customer(
    session: Session,
    order_id: int,
    customer_id: int,
) -> Order:
    order = session.get(Order, order_id)

    if order is None:
        raise ValueError("Pedido não encontrado.")

    if order.status != "DRAFT":
        raise ValueError(
            "Só é possível alterar o cliente de pedidos em DRAFT."
        )

    customer_exists = session.get(Customer, customer_id)

    if customer_exists is None:
        raise ValueError("Cliente não encontrado.")

    order.customer_id = customer_id

    session.flush()

    return order


def set_order_delivery_address(
    session: Session,
    order_id: int,
    address_id: int,
) -> Order:
    order = session.get(Order, order_id)

    if order is None:
        raise ValueError("Pedido não encontrado.")

    if order.status != "DRAFT":
        raise ValueError(
            "Só é possível alterar o endereço de pedidos em DRAFT."
        )

    if order.customer_id is None:
        raise ValueError(
            "O pedido precisa ter um cliente antes de definir o endereço."
        )

    address = session.scalar(
        select(CustomerAddress).where(
            CustomerAddress.id == address_id,
            CustomerAddress.customer_id == order.customer_id,
        )
    )

    if address is None:
        raise ValueError(
            "Endereço não encontrado para este cliente."
        )

    delivery_fee = _get_delivery_zone_fee(
        session,
        address.neighborhood,
    )

    delivery_fee = calculate_delivery_fee(
        delivery_method="DELIVERY",
        delivery_fee=delivery_fee,
    )

    order.delivery_method = "DELIVERY"
    order.delivery_fee = delivery_fee

    order.delivery_zip_code = address.zip_code
    order.delivery_street = address.street
    order.delivery_number = address.number
    order.delivery_complement = address.complement
    order.delivery_neighborhood = address.neighborhood
    order.delivery_reference = address.reference

    recalculate_order_totals(session, order)

    return order


def transition_order_status(
    session: Session,
    order_id: int,
    new_status: str,
) -> Order:
    order = session.get(Order, order_id)

    if order is None:
        raise ValueError("Pedido não encontrado.")

    current_status = order.status

    validate_order_status_transition(
        current_status,
        new_status,
    )

    if (
        current_status == "PREPARING"
        and new_status == "OUT_FOR_DELIVERY"
        and order.delivery_method != "DELIVERY"
    ):
        raise ValueError(
            "Somente pedidos de entrega podem sair para entrega."
        )

    if (
        current_status == "PREPARING"
        and new_status == "READY_FOR_PICKUP"
        and order.delivery_method != "PICKUP"
    ):
        raise ValueError(
            "Somente pedidos de retirada podem ficar prontos para retirada."
        )

    history = OrderStatusHistory(
        order_id=order.id,
        from_status=current_status,
        to_status=new_status,
    )

    order.status = new_status

    session.add(history)
    session.flush()

    return order