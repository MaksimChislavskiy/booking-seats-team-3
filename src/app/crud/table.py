from app.crud.base import CRUDBase
from app.models import Table


class CRUDTable(CRUDBase):
    """CRUD для столов."""


table_crud = CRUDTable(Table)
