from enum import StrEnum


class BookingStatus(StrEnum):
    """Статусы бронирования."""

    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
