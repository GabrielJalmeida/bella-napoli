from sqlalchemy import URL, create_engine

from app.core.config import settings


database_url = URL.create(
	drivername="postgresql+psycopg",
	username=settings.db_user,
	password=settings.db_password,
	host=settings.db_host,
	port=settings.db_port,
	database=settings.db_name,
)

engine = create_engine(database_url)