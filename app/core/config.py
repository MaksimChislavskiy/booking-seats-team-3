from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Содержит основные настройки проекта."""

    app_title: str = 'Система бронирования мест в кафе'
    app_description: str = 'Сервис для бронирования мест в кафе'


settings = Settings()
