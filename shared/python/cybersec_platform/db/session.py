from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class Settings(BaseSettings):
    """EN: Application settings shared by API, workers, and service processes.
    RU: Настройки приложения, общие для API, воркеров и сервисных процессов.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./cybersec.db"
    sync_database_url: str = "sqlite:///./cybersec.db"
    redis_url: str = "redis://localhost:6379/0"
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"
    rabbitmq_url: str | None = None
    celery_broker_url: str | None = None
    celery_result_backend: str = "redis://localhost:6379/1"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 1440
    backend_cors_origins: str = "http://localhost:3000"
    inference_service_url: str = "http://localhost:8001"
    log_service_url: str = "http://log-service:8002"
    data_processing_service_url: str = "http://data-processing-service:8003"
    data_root: str = "./app-data"
    raw_data_path: str = "./app-data/raw"
    archive_data_path: str = "./app-data/archives"
    parsed_data_path: str = "./app-data/parsed"
    normalized_data_path: str = "./app-data/normalized"
    staging_database_url: str | None = None
    staging_sync_database_url: str | None = None
    normalized_database_url: str | None = None
    normalized_sync_database_url: str | None = None
    models_path: str = "./app-data/models"
    reports_path: str = "./app-data/reports"
    explanations_path: str = "./app-data/explanations"
    logs_path: str = "./app-data/logs"
    tmp_path: str = "./app-data/tmp"
    language_en_path: str = "./app-data/languages/en.json"
    language_ru_path: str = "./app-data/languages/ru.json"
    default_admin_email: str = "admin@example.com"
    default_admin_password: str = "admin123456"
    outbox_poll_interval_ms: int = 5000
    outbox_publish_batch_size: int = 10
    outbox_max_attempts: int = 10

    @model_validator(mode="after")
    def apply_runtime_defaults(self) -> "Settings":
        if not self.rabbitmq_url:
            quoted_user = quote(self.rabbitmq_user, safe="")
            quoted_password = quote(self.rabbitmq_password, safe="")
            quoted_vhost = quote(self.rabbitmq_vhost, safe="/")
            self.rabbitmq_url = (
                f"amqp://{quoted_user}:{quoted_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/{quoted_vhost}"
            )
        if not self.celery_broker_url:
            self.celery_broker_url = self.rabbitmq_url
        if not self.staging_database_url:
            self.staging_database_url = self.database_url
        if not self.staging_sync_database_url:
            self.staging_sync_database_url = self.sync_database_url
        if not self.normalized_database_url:
            self.normalized_database_url = self.database_url
        if not self.normalized_sync_database_url:
            self.normalized_sync_database_url = self.sync_database_url
        return self


@lru_cache
def get_settings() -> Settings:
    """EN: Return cached environment-backed settings for the current process.
    RU: Возвращает кешированные настройки процесса, построенные из окружения.
    """

    return Settings()


def get_engine():
    """EN: Build the async SQLAlchemy engine.
    RU: Создаёт асинхронный SQLAlchemy engine.
    """

    settings = get_settings()
    return create_async_engine(settings.database_url, future=True, echo=False)


def get_sync_engine():
    """EN: Build the synchronous SQLAlchemy engine used for administrative tasks.
    RU: Создаёт синхронный SQLAlchemy engine для административных операций.
    """

    settings = get_settings()
    return create_engine(settings.sync_database_url, future=True, echo=False)


def ensure_database_exists() -> None:
    """EN: Create the target PostgreSQL database when it is missing.
    RU: Создаёт целевую базу PostgreSQL, если она отсутствует.
    """

    settings = get_settings()
    database_url = make_url(settings.sync_database_url)

    if not database_url.drivername.startswith("postgresql") or not database_url.database:
        return

    target_database = database_url.database
    admin_database = "postgres"
    admin_url = _with_database(database_url, admin_database)

    with create_engine(admin_url, future=True, isolation_level="AUTOCOMMIT").connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
            {"database_name": target_database},
        ).scalar()
        if exists:
            return

        quoted_database_name = target_database.replace('"', '""')
        connection.exec_driver_sql(f'CREATE DATABASE "{quoted_database_name}"')


def _with_database(url: URL, database_name: str) -> URL:
    """EN: Return a copy of URL pointing to another database.
    RU: Возвращает копию URL, указывающую на другую базу данных.
    """

    return url.set(database=database_name)


async_session_factory = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)


async def get_async_session() -> AsyncSession:
    """EN: Yield an async database session for request or task scope.
    RU: Предоставляет асинхронную сессию БД для запроса или задачи.
    """

    async with async_session_factory() as session:
        yield session
