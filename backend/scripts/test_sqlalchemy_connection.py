from sqlalchemy import text

from app.db.database import engine


def main():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_user, current_database();")
        )

        current_user, current_database = result.one()

        print("SQLAlchemy conectado com sucesso!")
        print(f"Usuário: {current_user}")
        print(f"Banco: {current_database}")


if __name__ == "__main__":
    main()