from sqlalchemy.orm import Session

import pytest

from app.db.database import engine
from app.models.customer_address import CustomerAddress
from app.services.customer_addresses import (
    create_customer_address,
    delete_customer_address,
    update_customer_address,
)
from app.services.customers import create_customer


@pytest.fixture
def session():
    session = Session(engine)

    try:
        yield session
    finally:
        session.rollback()
        session.close()


def create_test_customer(session: Session):
    return create_customer(
        session,
        name="Cliente Teste",
        phone="11999999999",
    )


def test_create_customer_address(session: Session):
    customer = create_test_customer(session)

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

    assert address.id is not None
    assert address.customer_id == customer.id
    assert address.zip_code == "03123000"
    assert address.street == "Rua Bella Napoli"
    assert address.number == "214"
    assert address.neighborhood == "Mooca"
    assert address.complement == "Casa 2"
    assert address.reference == "Próximo à praça"


def test_create_customer_address_without_optional_fields(
    session: Session,
):
    customer = create_test_customer(session)

    address = create_customer_address(
        session,
        customer_id=customer.id,
        zip_code="03123000",
        street="Rua Bella Napoli",
        number="214",
        neighborhood="Mooca",
    )

    assert address.complement is None
    assert address.reference is None


def test_create_customer_address_normalizes_spaces(
    session: Session,
):
    customer = create_test_customer(session)

    address = create_customer_address(
        session,
        customer_id=customer.id,
        zip_code=" 03123000 ",
        street=" Rua Bella Napoli ",
        number=" 214 ",
        neighborhood=" Mooca ",
        complement="  Casa 2  ",
        reference="   ",
    )

    assert address.zip_code == "03123000"
    assert address.street == "Rua Bella Napoli"
    assert address.number == "214"
    assert address.neighborhood == "Mooca"
    assert address.complement == "Casa 2"
    assert address.reference is None


def test_create_customer_address_rejects_unknown_customer(
    session: Session,
):
    with pytest.raises(
        ValueError,
        match="Cliente não encontrado",
    ):
        create_customer_address(
            session,
            customer_id=999999,
            zip_code="03123000",
            street="Rua Bella Napoli",
            number="214",
            neighborhood="Mooca",
        )


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("zip_code", "CEP"),
        ("street", "rua"),
        ("number", "número"),
        ("neighborhood", "bairro"),
    ],
)
def test_create_customer_address_rejects_required_empty_fields(
    session: Session,
    field: str,
    message: str,
):
    customer = create_test_customer(session)

    values = {
        "zip_code": "03123000",
        "street": "Rua Bella Napoli",
        "number": "214",
        "neighborhood": "Mooca",
    }

    values[field] = "   "

    with pytest.raises(
        ValueError,
        match=message,
    ):
        create_customer_address(
            session,
            customer_id=customer.id,
            **values,
        )

def test_update_customer_address(session: Session):
    customer = create_test_customer(session)

    address = create_customer_address(
        session,
        customer_id=customer.id,
        zip_code="03123000",
        street="Rua Bella Napoli",
        number="214",
        neighborhood="Mooca",
    )

    updated_address = update_customer_address(
        session,
        customer_id=customer.id,
        address_id=address.id,
        zip_code="03333000",
        street="Rua Nova",
        number="500",
        neighborhood="Tatuapé",
        complement="Apartamento 12",
        reference="Perto do metrô",
    )

    assert updated_address.id == address.id
    assert updated_address.customer_id == customer.id
    assert updated_address.zip_code == "03333000"
    assert updated_address.street == "Rua Nova"
    assert updated_address.number == "500"
    assert updated_address.neighborhood == "Tatuapé"
    assert updated_address.complement == "Apartamento 12"
    assert updated_address.reference == "Perto do metrô"


def test_update_customer_address_rejects_other_customer(
    session: Session,
):
    customer_a = create_test_customer(session)

    customer_b = create_customer(
        session,
        name="Outro Cliente",
        phone="11955555555",
    )

    address_a = create_customer_address(
        session,
        customer_id=customer_a.id,
        zip_code="03123000",
        street="Rua Bella Napoli",
        number="214",
        neighborhood="Mooca",
    )

    with pytest.raises(
        ValueError,
        match="Endereço não encontrado",
    ):
        update_customer_address(
            session,
            customer_id=customer_b.id,
            address_id=address_a.id,
            zip_code="03333000",
            street="Rua Nova",
            number="500",
            neighborhood="Tatuapé",
        )


def test_update_customer_address_rejects_empty_required_fields(
    session: Session,
):
    customer = create_test_customer(session)

    address = create_customer_address(
        session,
        customer_id=customer.id,
        zip_code="03123000",
        street="Rua Bella Napoli",
        number="214",
        neighborhood="Mooca",
    )

    with pytest.raises(
        ValueError,
        match="rua",
    ):
        update_customer_address(
            session,
            customer_id=customer.id,
            address_id=address.id,
            zip_code="03123000",
            street="   ",
            number="214",
            neighborhood="Mooca",
        )

def test_delete_customer_address(session: Session):
    customer = create_test_customer(session)

    address = create_customer_address(
        session,
        customer_id=customer.id,
        zip_code="03123000",
        street="Rua Bella Napoli",
        number="214",
        neighborhood="Mooca",
    )

    delete_customer_address(
        session,
        customer_id=customer.id,
        address_id=address.id,
    )

    assert session.get(CustomerAddress, address.id) is None


def test_delete_customer_address_rejects_other_customer(
    session: Session,
):
    customer_a = create_test_customer(session)

    customer_b = create_customer(
        session,
        name="Outro Cliente",
        phone="11955555555",
    )

    address_a = create_customer_address(
        session,
        customer_id=customer_a.id,
        zip_code="03123000",
        street="Rua Bella Napoli",
        number="214",
        neighborhood="Mooca",
    )

    with pytest.raises(
        ValueError,
        match="Endereço não encontrado",
    ):
        delete_customer_address(
            session,
            customer_id=customer_b.id,
            address_id=address_a.id,
        )

    assert session.get(CustomerAddress, address_a.id) is not None