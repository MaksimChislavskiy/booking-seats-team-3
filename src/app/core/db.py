from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import (DeclarativeBase, Mapped, declared_attr,
                            mapped_column)

from app.core.config import settings


class Base(DeclarativeBase):
    """Базовый класс с автоматическим определением имени таблицы и поля id."""

    @declared_attr
    def __tablename__(cls) -> str:  # noqa: N805
        return cls.__name__.lower()

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        index=True,
    )


engine = create_async_engine(settings.database_url)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_async_session() -> AsyncSession:
    """Асинхронный генератор сессии SQLAlchemy."""
    async with AsyncSessionLocal() as async_session:
        yield async_session
