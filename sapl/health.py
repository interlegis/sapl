# core/health.py
import logging
import time
from typing import Tuple, Optional
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger(__name__)


def check_app() -> Tuple[bool, Optional[str], float]:
    t0 = time.monotonic()
    return True, None, (time.monotonic() - t0) * 1000


def check_db() -> Tuple[bool, Optional[str], float]:
    t0 = time.monotonic()
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True, None, (time.monotonic() - t0) * 1000
    except Exception as e:
        logging.error(e)
        return False, "An internal error has occurred!", (time.monotonic() - t0) * 1000


def check_cache() -> Tuple[bool, Optional[str], float]:
    t0 = time.monotonic()
    try:
        cache.set("_hc", "1", 5)
        ok = cache.get("_hc") == "1"
        return ok, None if ok else "Cache get/set failed", (time.monotonic() - t0) * 1000
    except Exception as e:
        logging.error(e)
        return False, "An internal error has occurred!", (time.monotonic() - t0) * 1000
