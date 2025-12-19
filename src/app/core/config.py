import os

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import (
    DEFAULT_LOCAL_HOST,
    ENV_RUN_IN_DOCKER,
    INFRA_DIR,
    TRUE_VALUE,
)

IS_RUN_IN_DOCKER = os.getenv(ENV_RUN_IN_DOCKER, 'no').lower() == TRUE_VALUE


class Settings(BaseSettings):
    """Содержит основные настройки проекта."""

    app_title: str = 'Система бронирования мест в кафе'
    app_description: str = 'Сервис для бронирования мест в кафе'
    first_superuser_email: EmailStr | None = None
    first_superuser_password: str | None = None
    log_level: str = 'INFO'

    secret: str = 'SECRET'
    access_token_expire_seconds: int = 3600

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: str

    model_config = SettingsConfigDict(
        env_file=None if IS_RUN_IN_DOCKER else INFRA_DIR / '.env',
        env_file_encoding='utf-8',
    )

    @property
    def database_url(self) -> str:
        """Динамически формирует URL для подключения к БД."""
        host = self.postgres_host if IS_RUN_IN_DOCKER else DEFAULT_LOCAL_HOST
        return (
            f'postgresql+asyncpg://{self.postgres_user}:'
            f'{self.postgres_password}@{host}:'
            f'{self.postgres_port}/{self.postgres_db}'
        )


settings = Settings()
