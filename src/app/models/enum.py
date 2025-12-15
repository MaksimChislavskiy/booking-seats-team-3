import enum


class BookingStatus(str, enum.Enum):
    """Статусы бронирования."""

    pending = 'pending'
    confirmed = 'confirmed'
    cancelled = 'cancelled'
