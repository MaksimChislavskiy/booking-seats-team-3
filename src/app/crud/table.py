from app.crud.base import CRUDBase
from app.models import Table
from app.schemas import TableCreate, TableUpdate


class CRUDTable(CRUDBase[Table, TableCreate, TableUpdate]):
    """Заглушка."""


table_crud = CRUDTable(Table)
