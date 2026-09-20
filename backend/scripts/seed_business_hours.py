from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.business_hours import BusinessHours


BUSINESS_HOURS = [
    (0, True, None, None),                  # Segunda
    (1, False, time(18, 0), time(23, 0)),  # Terça
    (2, False, time(18, 0), time(23, 0)),  # Quarta
    (3, False, time(18, 0), time(23, 0)),  # Quinta
    (4, False, time(18, 0), time(0, 0)),   # Sexta
    (5, False, time(18, 0), time(0, 0)),   # Sábado
    (6, False, time(18, 0), time(23, 0)),  # Domingo
]


def seed_business_hours():
    with Session(engine) as session:
        for day_of_week, is_closed, open_time, close_time in BUSINESS_HOURS:
            existing_hours = session.scalar(
                select(BusinessHours).where(
                    BusinessHours.day_of_week == day_of_week
                )
            )

            if existing_hours is not None:
                print(f"Já existe: dia {day_of_week}")
                continue

            hours = BusinessHours(
                day_of_week=day_of_week,
                is_closed=is_closed,
                open_time=open_time,
                close_time=close_time,
            )

            session.add(hours)

            if is_closed:
                print(f"Criando: dia {day_of_week} - fechado")
            else:
                print(
                    f"Criando: dia {day_of_week} - "
                    f"{open_time.strftime('%H:%M')}–"
                    f"{close_time.strftime('%H:%M')}"
                )

        session.commit()

    print("Seed de horários concluído.")


if __name__ == "__main__":
    seed_business_hours()