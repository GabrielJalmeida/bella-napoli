from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.delivery_zone import DeliveryZone


DELIVERY_ZONES = [
    ("Mooca", Decimal("4.90")),
    ("Belém", Decimal("5.90")),
    ("Brás", Decimal("6.90")),
    ("Água Rasa", Decimal("6.90")),
    ("Tatuapé", Decimal("7.90")),
]


def seed_delivery_zones():
    with Session(engine) as session:
        for neighborhood, fee in DELIVERY_ZONES:
            existing_zone = session.scalar(
                select(DeliveryZone).where(
                    DeliveryZone.neighborhood == neighborhood
                )
            )

            if existing_zone is not None:
                print(f"Já existe: {neighborhood}")
                continue

            zone = DeliveryZone(
                neighborhood=neighborhood,
                fee=fee,
                active=True,
            )

            session.add(zone)
            print(f"Criando: {neighborhood} - R$ {fee:.2f}")

        session.commit()

    print("Seed de zonas de entrega concluído.")


if __name__ == "__main__":
    seed_delivery_zones()