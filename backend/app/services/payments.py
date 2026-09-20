import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.payment import (
    validate_cash_payment,
    validate_payment_amount,
    validate_payment_method,
)
from app.models.order import Order
from app.models.payment import Payment


PIX_EXPIRATION_MINUTES = 5


def _generate_pix_token(session: Session) -> str:
    """
    Gera um token PIX seguro e único.
    """

    while True:
        token = secrets.token_urlsafe(32)

        existing_payment = session.scalar(
            select(Payment).where(
                Payment.pix_token == token
            )
        )

        if existing_payment is None:
            return token


def create_payment_attempt(
    session: Session,
    order_id: int,
    method: str,
    change_for: Decimal | None = None,
) -> Payment:
    """
    Cria uma nova tentativa de pagamento.

    O valor do pagamento sempre vem de Order.total.
    """

    validate_payment_method(method)

    order = session.scalar(
        select(Order).where(
            Order.id == order_id
        )
    )

    if order is None:
        raise ValueError("Pedido não encontrado.")

    if order.total <= 0:
        raise ValueError(
            "Não é possível criar pagamento para um pedido com total zero."
        )

    amount = order.total

    validate_payment_amount(amount)

    if method == "CASH":
        validate_cash_payment(
            amount=amount,
            change_for=change_for,
        )
    elif change_for is not None:
        raise ValueError(
            "Troco somente pode ser informado para pagamento em dinheiro."
        )

    payment = Payment(
        order_id=order.id,
        method=method,
        status="PENDING",
        amount=amount,
        change_for=change_for,
    )

    if method == "PIX_DEMO":
        payment.pix_token = _generate_pix_token(session)

        payment.expires_at = (
            datetime.now(timezone.utc)
            + timedelta(minutes=PIX_EXPIRATION_MINUTES)
        )

    session.add(payment)
    session.flush()

    return payment


def expire_pix_payment(
    session: Session,
    payment_id: int,
    current_datetime: datetime | None = None,
) -> Payment:
    """
    Expira um pagamento PIX pendente.

    Permite receber current_datetime para que os testes
    sejam determinísticos.
    """

    payment = session.scalar(
        select(Payment).where(
            Payment.id == payment_id
        )
    )

    if payment is None:
        raise ValueError("Pagamento não encontrado.")

    if payment.method != "PIX_DEMO":
        raise ValueError(
            "Somente pagamentos PIX possuem expiração."
        )

    if payment.status == "PAID":
        return payment

    if payment.status != "PENDING":
        return payment

    if payment.expires_at is None:
        raise ValueError(
            "Pagamento PIX sem data de expiração."
        )

    if current_datetime is None:
        current_datetime = datetime.now(timezone.utc)

    if current_datetime.tzinfo is None:
        raise ValueError(
            "A data e hora precisam possuir timezone."
        )

    if current_datetime < payment.expires_at:
        raise ValueError(
            "O pagamento PIX ainda não expirou."
        )

    payment.status = "EXPIRED"

    session.flush()

    return payment


def confirm_pix_payment(
    session: Session,
    pix_token: str,
    current_datetime: datetime | None = None,
) -> Payment:
    """
    Confirma um pagamento PIX.

    Operação idempotente:
        PENDING → PAID
        PAID → PAID

    Se estiver vencido:
        PENDING → EXPIRED
    """

    if not pix_token:
        raise ValueError(
            "Token PIX não informado."
        )

    payment = session.scalar(
        select(Payment).where(
            Payment.pix_token == pix_token
        )
    )

    if payment is None:
        raise ValueError(
            "Pagamento PIX não encontrado."
        )

    if payment.method != "PIX_DEMO":
        raise ValueError(
            "O pagamento informado não é PIX."
        )

    if payment.status == "PAID":
        return payment

    if payment.status in {"EXPIRED", "CANCELLED"}:
        raise ValueError(
            f"Pagamento não pode ser confirmado no status {payment.status}."
        )

    if payment.status != "PENDING":
        raise ValueError(
            f"Status de pagamento inválido para confirmação: {payment.status}."
        )

    if payment.expires_at is None:
        raise ValueError(
            "Pagamento PIX sem data de expiração."
        )

    if current_datetime is None:
        current_datetime = datetime.now(timezone.utc)

    if current_datetime.tzinfo is None:
        raise ValueError(
            "A data e hora precisam possuir timezone."
        )

    if current_datetime >= payment.expires_at:
        payment.status = "EXPIRED"
        session.flush()

        raise ValueError(
            "O pagamento PIX expirou."
        )

    payment.status = "PAID"
    payment.paid_at = current_datetime

    session.flush()

    return payment