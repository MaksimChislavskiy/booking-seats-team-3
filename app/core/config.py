from pydantic import EmailStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Содержит основные настройки проекта."""

    app_title: str = 'Система бронирования мест в кафе'
    app_description: str = 'Сервис для бронирования мест в кафе'
    first_superuser_email: EmailStr | None = None
    first_superuser_password: str | None = None

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_server: str
    postgres_port: str

    @property
    def database_url(self) -> str:
        """Динамически формирует URL для подключения к БД."""
        return (
            f'postgresql+asyncpg://{self.postgres_user}:'
            f'{self.postgres_password}@{self.postgres_server}:'
            f'{self.postgres_port}/{self.postgres_db}'
        )

    class Config:
        """Конфигурация приложения."""

        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
