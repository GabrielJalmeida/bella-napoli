import re

from app.models.order_status_history import OrderStatusHistory
from app.services.customer_addresses import create_customer_address
from app.services.customers import create_customer
from app.services.orders import (
    create_draft_order,
    generate_order_code,
    set_order_customer,
    set_order_delivery,
    set_order_delivery_address,
    transition_order_status,
)

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.database import engine



def test_codigo_do_pedido_tem_formato_valido():
    code = generate_order_code()

    assert re.fullmatch(
        r"BN-[A-Z2-9]{8}",
        code,
    )


def test_codigo_do_pedido_nao_usa_caracteres_ambiguos():
    for _ in range(100):
        code = generate_order_code()

        assert "I" not in code
        assert "O" not in code
        assert "0" not in code
        assert "1" not in code

@pytest.fixture
def session():
    session = Session(engine)

    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_set_order_delivery_pickup(session: Session):
    order = create_draft_order(session)

    set_order_delivery(
        session,
        order_id=order.id,
        delivery_method="PICKUP",
    )

    assert order.delivery_method == "PICKUP"
    assert order.delivery_neighborhood is None
    assert order.delivery_fee == Decimal("0.00")
    assert order.total == Decimal("0.00")


def test_set_order_delivery_mooca(session: Session):
    order = create_draft_order(session)

    set_order_delivery(
        session,
        order_id=order.id,
        delivery_method="DELIVERY",
        neighborhood="Mooca",
    )

    assert order.delivery_method == "DELIVERY"
    assert order.delivery_neighborhood == "Mooca"
    assert order.delivery_fee == Decimal("4.90")
    assert order.total == Decimal("4.90")


def test_set_order_delivery_tatuape(session: Session):
    order = create_draft_order(session)

    set_order_delivery(
        session,
        order_id=order.id,
        delivery_method="DELIVERY",
        neighborhood="Tatuapé",
    )

    assert order.delivery_fee == Decimal("7.90")
    assert order.total == Decimal("7.90")


def test_set_delivery_requires_neighborhood(session: Session):
    order = create_draft_order(session)

    with pytest.raises(
        ValueError,
        match="bairro",
    ):
        set_order_delivery(
            session,
            order_id=order.id,
            delivery_method="DELIVERY",
        )


def test_pickup_rejects_neighborhood(session: Session):
    order = create_draft_order(session)

    with pytest.raises(
        ValueError,
        match="Retirada",
    ):
        set_order_delivery(
            session,
            order_id=order.id,
            delivery_method="PICKUP",
            neighborhood="Mooca",
        )


def test_set_delivery_rejects_unsupported_neighborhood(session: Session):
    order = create_draft_order(session)

    with pytest.raises(
        ValueError,
        match="atendida",
    ):
        set_order_delivery(
            session,
            order_id=order.id,
            delivery_method="DELIVERY",
            neighborhood="Santos",
        )


def test_set_delivery_rejects_non_draft_order(session: Session):
    order = create_draft_order(session)

    order.status = "CONFIRMED"
    session.flush()

    with pytest.raises(
        ValueError,
        match="DRAFT",
    ):
        set_order_delivery(
            session,
            order_id=order.id,
            delivery_method="DELIVERY",
            neighborhood="Mooca",
        )

def test_set_order_customer(session: Session):
    order = create_draft_order(session)

    customer = create_customer(
        session,
        name="Maria Silva",
        phone="11988888888",
    )

    set_order_customer(
        session,
        order_id=order.id,
        customer_id=customer.id,
    )

    assert order.customer_id == customer.id


def test_set_order_customer_rejects_unknown_customer(
    session: Session,
):
    order = create_draft_order(session)

    with pytest.raises(
        ValueError,
        match="Cliente não encontrado",
    ):
        set_order_customer(
            session,
            order_id=order.id,
            customer_id=999999,
        )


def test_set_order_customer_rejects_non_draft_order(
    session: Session,
):
    order = create_draft_order(session)

    customer = create_customer(
        session,
        name="João Silva",
        phone="11977777777",
    )

    order.status = "CONFIRMED"
    session.flush()

    with pytest.raises(
        ValueError,
        match="DRAFT",
    ):
        set_order_customer(
            session,
            order_id=order.id,
            customer_id=customer.id,
        )

def test_set_order_delivery_address_creates_snapshot(
    session: Session,
):
    order = create_draft_order(session)

    customer = create_customer(
        session,
        name="Maria Silva",
        phone="11988888888",
    )

    set_order_customer(
        session,
        order_id=order.id,
        customer_id=customer.id,
    )

    address = create_customer_address(
        session,
        customer_id=customer.id,
        zip_code="03123000",
        street="Rua Bella Napoli",
        number="214",
        neighborhood="Mooca",
        complement="Casa 2",
        reference="Próximo à praça",
    )

    set_order_delivery_address(
        session,
        order_id=order.id,
        address_id=address.id,
    )

    assert order.delivery_method == "DELIVERY"
    assert order.delivery_fee == Decimal("4.90")

    assert order.delivery_zip_code == "03123000"
    assert order.delivery_street == "Rua Bella Napoli"
    assert order.delivery_number == "214"
    assert order.delivery_complement == "Casa 2"
    assert order.delivery_neighborhood == "Mooca"
    assert order.delivery_reference == "Próximo à praça"


def test_set_delivery_address_requires_customer(
    session: Session,
):
    order = create_draft_order(session)

    with pytest.raises(
        ValueError,
        match="cliente",
    ):
        set_order_delivery_address(
            session,
            order_id=order.id,
            address_id=1,
        )


def test_set_delivery_address_rejects_other_customer_address(
    session: Session,
):
    order = create_draft_order(session)

    customer_a = create_customer(
        session,
        name="Cliente A",
        phone="11911111111",
    )

    customer_b = create_customer(
        session,
        name="Cliente B",
        phone="11922222222",
    )

    set_order_customer(
        session,
        order_id=order.id,
        customer_id=customer_a.id,
    )

    address_b = create_customer_address(
        session,
        customer_id=customer_b.id,
        zip_code="03123000",
        street="Rua Bella Napoli",
        number="214",
        neighborhood="Mooca",
    )

    with pytest.raises(
        ValueError,
        match="Endereço não encontrado",
    ):
        set_order_delivery_address(
            session,
            order_id=order.id,
            address_id=address_b.id,
        )


def test_set_delivery_address_recalculates_total(
    session: Session,
):
    order = create_draft_order(session)

    customer = create_customer(
        session,
        name="João Silva",
        phone="11933333333",
    )

    set_order_customer(
        session,
        order_id=order.id,
        customer_id=customer.id,
    )

    address = create_customer_address(
        session,
        customer_id=customer.id,
        zip_code="03123000",
        street="Rua Bella Napoli",
        number="214",
        neighborhood="Mooca",
    )

    set_order_delivery_address(
        session,
        order_id=order.id,
        address_id=address.id,
    )

    assert order.subtotal == Decimal("0.00")
    assert order.delivery_fee == Decimal("4.90")
    assert order.total == Decimal("4.90")

def test_order_address_snapshot_is_independent_from_customer_address(
    session: Session,
):
    order = create_draft_order(session)

    customer = create_customer(
        session,
        name="Cliente Snapshot",
        phone="11944444444",
    )

    set_order_customer(
        session,
        order_id=order.id,
        customer_id=customer.id,
    )

    address = create_customer_address(
        session,
        customer_id=customer.id,
        zip_code="03123000",
        street="Rua Bella Napoli",
        number="214",
        neighborhood="Mooca",
        complement="Casa 2",
        reference="Próximo à praça",
    )

    set_order_delivery_address(
        session,
        order_id=order.id,
        address_id=address.id,
    )

    assert order.delivery_street == "Rua Bella Napoli"
    assert order.delivery_number == "214"
    assert order.delivery_neighborhood == "Mooca"

    # Simula uma alteração posterior no cadastro do cliente.
    address.street = "Rua Nova"
    address.number = "500"
    address.neighborhood = "Tatuapé"
    session.flush()

    # O pedido continua com o snapshot antigo.
    assert order.delivery_street == "Rua Bella Napoli"
    assert order.delivery_number == "214"
    assert order.delivery_neighborhood == "Mooca"
    assert order.delivery_fee == Decimal("4.90")

def test_transition_order_status_creates_history(
    session: Session,
):
    order = create_draft_order(session)

    transition_order_status(
        session,
        order_id=order.id,
        new_status="CONFIRMED",
    )

    assert order.status == "CONFIRMED"

    history = session.scalar(
    select(OrderStatusHistory).where(
        OrderStatusHistory.order_id == order.id,
        OrderStatusHistory.from_status == "DRAFT",
        OrderStatusHistory.to_status == "CONFIRMED",
    )
)

    assert history is not None
    assert history.from_status == "DRAFT"
    assert history.to_status == "CONFIRMED"

def test_transition_order_status_rejects_invalid_transition(
    session: Session,
):
    order = create_draft_order(session)

    with pytest.raises(
        ValueError,
        match="não é permitida",
    ):
        transition_order_status(
            session,
            order_id=order.id,
            new_status="COMPLETED",
        )

    assert order.status == "DRAFT"

def test_preparing_delivery_can_go_out_for_delivery(
    session: Session,
):
    order = create_draft_order(session)

    order.delivery_method = "DELIVERY"
    session.flush()

    transition_order_status(
        session,
        order_id=order.id,
        new_status="CONFIRMED",
    )

    transition_order_status(
        session,
        order_id=order.id,
        new_status="PREPARING",
    )

    transition_order_status(
        session,
        order_id=order.id,
        new_status="OUT_FOR_DELIVERY",
    )

    assert order.status == "OUT_FOR_DELIVERY"

def test_preparing_pickup_can_go_to_ready_for_pickup(
    session: Session,
):
    order = create_draft_order(session)

    order.delivery_method = "PICKUP"
    session.flush()

    transition_order_status(
        session,
        order_id=order.id,
        new_status="CONFIRMED",
    )

    transition_order_status(
        session,
        order_id=order.id,
        new_status="PREPARING",
    )

    transition_order_status(
        session,
        order_id=order.id,
        new_status="READY_FOR_PICKUP",
    )

    assert order.status == "READY_FOR_PICKUP"

def test_delivery_order_cannot_be_marked_ready_for_pickup(
    session: Session,
):
    order = create_draft_order(session)

    order.delivery_method = "DELIVERY"
    session.flush()

    transition_order_status(
        session,
        order_id=order.id,
        new_status="CONFIRMED",
    )

    transition_order_status(
        session,
        order_id=order.id,
        new_status="PREPARING",
    )

    with pytest.raises(
        ValueError,
        match="retirada",
    ):
        transition_order_status(
            session,
            order_id=order.id,
            new_status="READY_FOR_PICKUP",
        )


def test_pickup_order_cannot_go_out_for_delivery(
    session: Session,
):
    order = create_draft_order(session)

    order.delivery_method = "PICKUP"
    session.flush()

    transition_order_status(
        session,
        order_id=order.id,
        new_status="CONFIRMED",
    )

    transition_order_status(
        session,
        order_id=order.id,
        new_status="PREPARING",
    )

    with pytest.raises(
        ValueError,
        match="entrega",
    ):
        transition_order_status(
            session,
            order_id=order.id,
            new_status="OUT_FOR_DELIVERY",
        )

def test_transition_order_status_records_full_history(
    session: Session,
):
    order = create_draft_order(session)

    order.delivery_method = "DELIVERY"
    session.flush()

    transition_order_status(
        session,
        order_id=order.id,
        new_status="CONFIRMED",
    )

    transition_order_status(
        session,
        order_id=order.id,
        new_status="PREPARING",
    )

    transition_order_status(
        session,
        order_id=order.id,
        new_status="OUT_FOR_DELIVERY",
    )

    transition_order_status(
        session,
        order_id=order.id,
        new_status="COMPLETED",
    )

    history = session.scalars(
        select(OrderStatusHistory)
        .where(
            OrderStatusHistory.order_id == order.id
        )
        .order_by(OrderStatusHistory.id)
    ).all()

    assert len(history) == 5

    assert history[0].from_status is None
    assert history[0].to_status == "DRAFT"

    assert history[1].from_status == "DRAFT"
    assert history[1].to_status == "CONFIRMED"

    assert history[2].from_status == "CONFIRMED"
    assert history[2].to_status == "PREPARING"

    assert history[3].from_status == "PREPARING"
    assert history[3].to_status == "OUT_FOR_DELIVERY"

    assert history[4].from_status == "OUT_FOR_DELIVERY"
    assert history[4].to_status == "COMPLETED"