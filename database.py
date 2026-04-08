import logging

from sqlmodel import SQLModel, create_engine

from config import settings

logger = logging.getLogger(__name__)

from sqlalchemy import event

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(
    settings.database_url,
    echo=settings.sql_debug,
    connect_args=connect_args,
)

if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    logger.info("Base de datos y tablas inicializadas correctamente.")
