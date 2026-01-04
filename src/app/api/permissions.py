# FIXME: Доделать логику  проверки на принадлежность к кафе и правам доступа
from fastapi import HTTPException, status

from app.models import User, UserRole


def can_manage_cafe(user: User, cafe_id: int) -> bool:
    """Проверяет, может ли пользователь управлять кафе.

    Правила:
    - ADMIN: всегда может
    - MANAGER: только если привязан к этому кафе
    - USER: не может
    """
    return user.role == UserRole.ADMIN or (
        user.role == UserRole.MANAGER and user.cafe_id == cafe_id
    )


def ensure_can_manage_cafe(user: User, cafe_id: int) -> None:
    if not can_manage_cafe(user, cafe_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав для управления этим кафе',
        )
