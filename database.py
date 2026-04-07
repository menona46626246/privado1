import logging

from sqlmodel import SQLModel, create_engine

from config import settings

logger = logging.getLogger(__name__)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(
    settings.database_url,
    echo=settings.sql_debug,
    connect_args=connect_args,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    logger.info("Base de datos y tablas inicializadas correctamente.")
