from sqlalchemy.orm import Session

import pytest

from app.db.database import engine
from app.services.customers import create_customer


@pytest.fixture
def session():
    session = Session(engine)

    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_create_customer(session: Session):
    customer = create_customer(
        session,
        name="  Gabriel Almeida  ",
        phone=" 11999999999 ",
        email=" gabriel@example.com ",
    )

    assert customer.id is not None
    assert customer.name == "Gabriel Almeida"
    assert customer.phone == "11999999999"
    assert customer.email == "gabriel@example.com"


def test_create_customer_without_email(session: Session):
    customer = create_customer(
        session,
        name="Maria Silva",
        phone="11988888888",
    )

    assert customer.name == "Maria Silva"
    assert customer.phone == "11988888888"
    assert customer.email is None


def test_create_customer_rejects_empty_name(session: Session):
    with pytest.raises(
        ValueError,
        match="nome",
    ):
        create_customer(
            session,
            name="   ",
            phone="11999999999",
        )


def test_create_customer_rejects_empty_phone(session: Session):
    with pytest.raises(
        ValueError,
        match="telefone",
    ):
        create_customer(
            session,
            name="Gabriel Almeida",
            phone="   ",
        )


def test_create_customer_empty_email_becomes_none(
    session: Session,
):
    customer = create_customer(
        session,
        name="João Silva",
        phone="11977777777",
        email="   ",
    )

    assert customer.email is None