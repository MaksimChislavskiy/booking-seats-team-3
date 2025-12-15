from sqlalchemy import Column, ForeignKey, Integer, Table, UniqueConstraint

from app.core.db import Base

"""Вспомогательная таблица для связи кафе и менеджеров.

Таблица реализует many-to-many связь между Cafe и User,
так как модель User не содержит прямого ForeignKey на Cafe.

Ограничения:
    - Составной первичный ключ (cafe_id, user_id) предотвращает
      дублирование одной и той же пары кафе–пользователь.
    - Уникальное ограничение на user_id гарантирует, что один пользователь
      может быть менеджером только одного кафе.
"""
cafe_managers = Table(
    'cafe_managers',
    Base.metadata,
    Column(
        'cafe_id',
        Integer,
        ForeignKey('cafe.id', ondelete='RESTRICT'),
        primary_key=True,
    ),
    Column(
        'user_id',
        Integer,
        ForeignKey('user.id', ondelete='RESTRICT'),
        primary_key=True,
    ),
    UniqueConstraint('user_id', name='uq_cafe_managers_user_id'),
)
