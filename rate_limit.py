"""Rate limiter shared across the app."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# In-memory storage is fine for single-node Mac server; can swap to redis:// later.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri="memory://",
)
