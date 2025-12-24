from app.crud.base import CRUDBase
from app.models.user import User


class UserCRUD(CRUDBase):
    """Заглушка."""

    pass


user_crud = UserCRUD(User)
