from app.crud.base import CRUDBase
from app.models import Cafe


class CafeCRUD(CRUDBase):
    """Заглушка для cafe_crud до реализации."""


cafe_crud = CafeCRUD(Cafe)
