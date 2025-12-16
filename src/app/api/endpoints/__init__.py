from .actions import router as actions_router
from .auth import router as auth_router
from .bookings import router as bookings_router
from .cafe import router as cafes_router
from .dishes import router as dishes_router
from .media import router as media_router
from .slots import router as slots_router
from .tables import router as tables_router
from .users import router as users_router

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
