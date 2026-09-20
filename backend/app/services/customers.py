from sqlalchemy.orm import Session

from app.models.customer import Customer


def create_customer(
    session: Session,
    name: str,
    phone: str,
    email: str | None = None,
) -> Customer:
    name = name.strip()
    phone = phone.strip()

    if not name:
        raise ValueError("O nome do cliente é obrigatório.")

    if not phone:
        raise ValueError("O telefone do cliente é obrigatório.")

    if email is not None:
        email = email.strip()

        if not email:
            email = None

    customer = Customer(
        name=name,
        phone=phone,
        email=email,
    )

    session.add(customer)
    session.flush()

    return customer