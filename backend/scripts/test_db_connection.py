import psycopg

from app.core.config import settings

def main():
	with psycopg.connect(
		host=settings.db_host,
		port=settings.db_port,
		dbname=settings.db_name,
		user=settings.db_user,
		password=settings.db_password,
	) as connection:
		with connection.cursor() as cursor:
			cursor.execute(
				"SELECT current_user, current_database();"
			)

			current_user, current_database = cursor.fetchone()

			print("Conexão realizada com sucesso!")
			print(f"Usuário: {current_user}")
			print(f"Banco: {current_database}")

if __name__ == "__main__":
	main()