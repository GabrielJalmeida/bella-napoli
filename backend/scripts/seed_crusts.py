from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.crust import Crust
from app.models.crust_price import CrustPrice


CRUSTS = {
    "Catupiry": {
        "P": Decimal("5.90"),
        "M": Decimal("7.90"),
        "G": Decimal("9.90"),
    },
    "Cheddar": {
        "P": Decimal("5.90"),
        "M": Decimal("7.90"),
        "G": Decimal("9.90"),
    },
    "Cream Cheese": {
        "P": Decimal("6.90"),
        "M": Decimal("8.90"),
        "G": Decimal("10.90"),
    },
}


def seed_crusts(session: Session) -> None:
    for crust_name, prices in CRUSTS.items():
        crust = session.scalar(
            select(Crust).where(
                Crust.name == crust_name
            )
        )

        if crust is None:
            crust = Crust(
                name=crust_name,
                active=True,
            )

            session.add(crust)
            session.flush()

            print(f"Borda criada: {crust.name}")

        else:
            print(f"Borda já existe: {crust.name}")

        for size, price in prices.items():
            crust_price = session.scalar(
                select(CrustPrice).where(
                    CrustPrice.crust_id == crust.id,
                    CrustPrice.size == size,
                )
            )

            if crust_price is None:
                session.add(
                    CrustPrice(
                        crust_id=crust.id,
                        size=size,
                        price=price,
                        active=True,
                    )
                )

                print(
                    f"  Preço criado: {size} = R$ {price}"
                )

            else:
                if crust_price.price != price:
                    print(
                        f"  Atualizando preço: "
                        f"{crust.name} {size} "
                        f"{crust_price.price} → {price}"
                    )

                    crust_price.price = price

                else:
                    print(
                        f"  Preço já existe: {size} = R$ {price}"
                    )


def main() -> None:
    with Session(engine) as session:
        seed_crusts(session)
        session.commit()

    print("Seed de bordas concluído.")


if __name__ == "__main__":
    main()