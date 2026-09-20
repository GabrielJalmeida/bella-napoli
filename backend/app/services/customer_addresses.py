from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.customer import Customer
from app.models.customer_address import CustomerAddress


def create_customer_address(
    session: Session,
    customer_id: int,
    zip_code: str,
    street: str,
    number: str,
    neighborhood: str,
    complement: str | None = None,
    reference: str | None = None,
) -> CustomerAddress:
    customer = session.get(Customer, customer_id)

    if customer is None:
        raise ValueError("Cliente não encontrado.")

    zip_code = zip_code.strip()
    street = street.strip()
    number = number.strip()
    neighborhood = neighborhood.strip()

    if complement is not None:
        complement = complement.strip() or None

    if reference is not None:
        reference = reference.strip() or None

    if not zip_code:
        raise ValueError("O CEP é obrigatório.")

    if not street:
        raise ValueError("A rua é obrigatória.")

    if not number:
        raise ValueError("O número é obrigatório.")

    if not neighborhood:
        raise ValueError("O bairro é obrigatório.")

    address = CustomerAddress(
        customer_id=customer.id,
        zip_code=zip_code,
        street=street,
        number=number,
        neighborhood=neighborhood,
        complement=complement,
        reference=reference,
    )

    session.add(address)
    session.flush()

    return address

def update_customer_address(
    session: Session,
    customer_id: int,
    address_id: int,
    zip_code: str,
    street: str,
    number: str,
    neighborhood: str,
    complement: str | None = None,
    reference: str | None = None,
) -> CustomerAddress:
    address = session.scalar(
        select(CustomerAddress).where(
            CustomerAddress.id == address_id,
            CustomerAddress.customer_id == customer_id,
        )
    )

    if address is None:
        raise ValueError(
            "Endereço não encontrado para este cliente."
        )

    zip_code = zip_code.strip()
    street = street.strip()
    number = number.strip()
    neighborhood = neighborhood.strip()

    if complement is not None:
        complement = complement.strip() or None

    if reference is not None:
        reference = reference.strip() or None

    if not zip_code:
        raise ValueError("O CEP é obrigatório.")

    if not street:
        raise ValueError("A rua é obrigatória.")

    if not number:
        raise ValueError("O número é obrigatório.")

    if not neighborhood:
        raise ValueError("O bairro é obrigatório.")

    address.zip_code = zip_code
    address.street = street
    address.number = number
    address.neighborhood = neighborhood
    address.complement = complement
    address.reference = reference

    session.flush()

    return address

def delete_customer_address(
    session: Session,
    customer_id: int,
    address_id: int,
) -> None:
    address = session.scalar(
        select(CustomerAddress).where(
            CustomerAddress.id == address_id,
            CustomerAddress.customer_id == customer_id,
        )
    )

    if address is None:
        raise ValueError(
            "Endereço não encontrado para este cliente."
        )

    session.delete(address)
    session.flush()