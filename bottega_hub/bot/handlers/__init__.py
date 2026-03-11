from .start import router as start_router
from .menu import router as menu_router
from .progress import router as progress_router
from .checkin import router as checkin_router
from .reward import router as reward_router
from .rules import router as rules_router
from .support import router as support_router
from .policy import router as policy_router
from .admin import router as admin_router
from .callbacks import router as callback_router

__all__ = [
    'start_router', 'menu_router', 'progress_router', 'checkin_router',
    'reward_router', 'rules_router', 'support_router', 'policy_router',
    'admin_router', 'callback_router'
]
