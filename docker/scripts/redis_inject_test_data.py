#!/usr/bin/env python3
"""
redis_inject_test_data.py — inject synthetic rate-limiter entries into Redis.

Purpose: validate that RateLimitMiddleware reads the expected key schema,
that Redis CLI / RedisInsight shows the right structure, and that blocking
logic fires correctly without waiting for real traffic.

Usage:
    # Against docker-compose Redis (default)
    python3 docker/scripts/redis_inject_test_data.py

    # Against a different host/port
    REDIS_URL=redis://localhost:6379 python3 docker/scripts/redis_inject_test_data.py

    # Clear all synthetic keys written by a previous run
    CLEAR=1 python3 docker/scripts/redis_inject_test_data.py

Key schema (DB 1 — rate limiter):
    rl:ip:{ip}:reqs          INCR counter  — anonymous request count (TTL 60s)
    rl:ip:{ip}:blocked       string "1"    — IP hard-blocked (TTL 300s)
    rl:{ns}:user:{uid}:reqs  INCR counter  — auth user request count (TTL 60s)
    rl:{ns}:user:{uid}:blocked string "1"  — user hard-blocked (TTL 300s)
    rl:{ns}:ip:{ip}:w:{bucket} INCR        — namespace/IP sliding window (TTL 120s)
"""

import os
import sys
import time
from decouple import config

# ── dependency check ──────────────────────────────────────────────────────
try:
    import redis
except ImportError:
    print("ERROR: redis-py not installed.  Run: pip install redis", file=sys.stderr)
    sys.exit(1)

# ── config ────────────────────────────────────────────────────────────────
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379")
RATELIMIT_DB = 1          # DB1 is the rate-limiter database
CLEAR = config("CLEAR", default="0").lower() in ("1", "true", "yes")

# Synthetic values — tweak to exercise different code paths
NAMESPACE = "sapl"        # POD_NAMESPACE value (hostname or k8s namespace)
ANON_WINDOW = 60          # seconds — must match settings.RATE_LIMITER_RATE period
AUTH_WINDOW = 60
BLOCK_TTL = 300

TEST_IPS = [
    "203.0.113.1",   # below threshold (20 reqs)
    "203.0.113.2",   # AT threshold (35 reqs — should trigger block)
    "203.0.113.3",   # already blocked
    "203.0.113.4",   # namespace/window counter near threshold
]

TEST_USERS = [
    {"uid": "42",  "reqs": 50,   "blocked": False},   # normal auth user
    {"uid": "99",  "reqs": 120,  "blocked": False},   # AT auth threshold
    {"uid": "7",   "reqs": 10,   "blocked": True},    # pre-blocked user
]

# ── helpers ───────────────────────────────────────────────────────────────

def key_ip_reqs(ip):
    return f"rl:ip:{ip}:reqs"

def key_ip_blocked(ip):
    return f"rl:ip:{ip}:blocked"

def key_user_reqs(ns, uid):
    return f"rl:{ns}:user:{uid}:reqs"

def key_user_blocked(ns, uid):
    return f"rl:{ns}:user:{uid}:blocked"

def key_ns_window(ns, ip, bucket):
    return f"rl:{ns}:ip:{ip}:w:{bucket}"


def write(r, key, value, ttl, label):
    if isinstance(value, int):
        pipe = r.pipeline()
        pipe.set(key, value, ex=ttl)
        pipe.execute()
    else:
        r.set(key, value, ex=ttl)
    print(f"  SET  {key!r} = {value!r}  EX {ttl}s  ({label})")


def delete_pattern(r, pattern):
    keys = r.keys(pattern)
    if keys:
        r.delete(*keys)
        print(f"  DEL  {len(keys)} keys matching {pattern!r}")
    else:
        print(f"  (no keys matching {pattern!r})")


# ── main ──────────────────────────────────────────────────────────────────

def main():
    r = redis.from_url(REDIS_URL, db=RATELIMIT_DB, decode_responses=True)
    try:
        r.ping()
    except redis.ConnectionError as exc:
        print(f"ERROR: cannot connect to Redis at {REDIS_URL}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Redis: {REDIS_URL}  DB={RATELIMIT_DB}  clear={CLEAR}")
    print()

    # ── clear mode ────────────────────────────────────────────────────────
    if CLEAR:
        print("=== Clearing synthetic test keys ===")
        for ip in TEST_IPS:
            delete_pattern(r, f"rl:ip:{ip}:*")
            delete_pattern(r, f"rl:{NAMESPACE}:ip:{ip}:*")
        for u in TEST_USERS:
            delete_pattern(r, f"rl:{NAMESPACE}:user:{u['uid']}:*")
        print("Done.")
        return

    # ── anonymous IP counters ─────────────────────────────────────────────
    print("=== Anonymous IP request counters (DB1) ===")
    write(r, key_ip_reqs(TEST_IPS[0]),  20,  ANON_WINDOW, "below threshold")
    write(r, key_ip_reqs(TEST_IPS[1]),  35,  ANON_WINDOW, "AT threshold → middleware will block on next req")
    write(r, key_ip_reqs(TEST_IPS[3]),  30,  ANON_WINDOW, "below threshold")
    print()

    # ── blocked IPs ───────────────────────────────────────────────────────
    print("=== Blocked IPs (DB1) ===")
    write(r, key_ip_blocked(TEST_IPS[2]), "1", BLOCK_TTL, "hard-blocked")
    print()

    # ── namespace/IP sliding window ───────────────────────────────────────
    print("=== Namespace/IP sliding window (DB1) ===")
    bucket = int(time.time() // ANON_WINDOW)
    write(r, key_ns_window(NAMESPACE, TEST_IPS[3], bucket), 34, ANON_WINDOW * 2,
          "near window threshold (next req triggers ua_rotation block)")
    print()

    # ── authenticated user counters ───────────────────────────────────────
    print("=== Authenticated user request counters (DB1) ===")
    for u in TEST_USERS:
        if not u["blocked"]:
            write(r, key_user_reqs(NAMESPACE, u["uid"]), u["reqs"], AUTH_WINDOW,
                  f"uid={u['uid']} reqs={u['reqs']}")
    print()

    # ── blocked users ─────────────────────────────────────────────────────
    print("=== Blocked users (DB1) ===")
    for u in TEST_USERS:
        if u["blocked"]:
            write(r, key_user_blocked(NAMESPACE, u["uid"]), "1", BLOCK_TTL,
                  f"uid={u['uid']} hard-blocked")
    print()

    # ── summary ───────────────────────────────────────────────────────────
    all_keys = r.keys("rl:*")
    print(f"=== DB{RATELIMIT_DB} now contains {len(all_keys)} rl:* keys ===")
    for k in sorted(all_keys):
        ttl = r.ttl(k)
        val = r.get(k)
        print(f"  {k!r:55s}  val={val!r:5}  ttl={ttl}s")


if __name__ == "__main__":
    main()
