from app.crud.base import CRUDBase
from app.models import Booking
from app.schemas import BookingCreate, BookingUpdate


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    """CRUD для модели Booking."""

    pass
