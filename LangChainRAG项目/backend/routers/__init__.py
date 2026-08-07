"""
Routers package: exports all API route modules so they can be imported
as a single ``from routers import auth_router, kb_router, session_router``.
"""

from routers.auth_router import router as auth_router
from routers.kb_router import router as kb_router
from routers.session_router import router as session_router
