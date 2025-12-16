from enum import StrEnum

from app.core.constants import CANCELLED, CONFIRMED, PENDING


class BookingStatus(StrEnum):
    """Статусы бронирования."""

    pending = PENDING
    confirmed = CONFIRMED
    cancelled = CANCELLED
