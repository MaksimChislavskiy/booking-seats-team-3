from app.crud.base import CRUDBase
from app.models import Cafe
from app.schemas import CafeCreate, CafeUpdate


class CRUDCafe(CRUDBase[Cafe, CafeCreate, CafeUpdate]):
    """CRUD для модели Cafe."""


cafe_crud = CRUDCafe(Cafe)
