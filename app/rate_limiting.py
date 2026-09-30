from slowapi import Limiter
from slowapi.util import get_remote_address

# A default ceiling applies to every route; sensitive routes carry a tighter
# explicit @limiter.limit decorator on top of it.
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
