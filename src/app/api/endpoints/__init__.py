from .action import router as actions_router
from .auth import router as auth_router
from .booking import router as bookings_router
from .cafe import router as cafes_router
from .dish import router as dishes_router
from .media import router as media_router
from .slot import router as slots_router
from .table import router as tables_router
from .user import router as users_router

__all__ = [
    'auth_router',
    'actions_router',
    'bookings_router',
    'cafes_router',
    'dishes_router',
    'media_router',
    'slots_router',
    'tables_router',
    'users_router',
]
