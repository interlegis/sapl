"""
RateLimitMiddleware — cross-pod rate limiting backed by shared Redis.

Decision flow (per request):
  Both /api/ and non-/api/ paths — checked first, before all else:
    -1. IP in rl:ip_prefix:blocked (prefix match)? → 403  (Forbidden — not a rate
        limit; an operator-curated permanent deny list, no Retry-After)
        (universal — applies to authenticated users too, like the UA bot checks)
  /api/ paths — handled by _handle_api:
    0a. OPTIONS?                → pass (CORS preflight must never be blocked)
    0b. rl:ip_prefix:blocked?   → 403  (prefix match; see -1 above)
    0c. rl:ip:<ip>:blocked?     → 429  (global block also covers /api/)
    0d. rl:api:ip:<ip>:blocked? → 429  (API-only block)
        Block checks 0b-0d always run before the same-origin check below —
        Origin/Referer are client-controlled and trivially spoofable, so they
        must never be able to override an already-made block decision.
    0e. Same-origin?            → pass, skipping 0f-0g only (SAPL's own polling
        is exempt from quota/rate-limit accounting, never from active blocks)
    0f. Daily/weekly quota exceeded? → 429
    0g. Anon + API threshold exceeded? → SET rl:api:ip:<ip>:blocked, 429
        (never writes rl:ip:<ip>:blocked)
    0h. Auth: falls through to _evaluate (per-user counter)
  Non-/api/ paths:
  1. Known bot UA?          → 429  (Python list — substring match)
  1b. Redis UA deny list?   → 429  (runtime SET — token hash match, refreshed every 60 s)
  2. Anonymous AND IP in blocked set? → 429  (authenticated users skip — have per-user limit at 3c)
  3. Authenticated user?
       a. User blocked?     → 429
       b. Suspicious hdrs?  → 429
       c. User rate ≥ 240?  → 429 (no persistent block; window resets after 60 s)
  4. Anonymous:
       a. Suspicious hdrs?  → 429
       b. IP rate ≥ 120/min? → SET RL_IP_BLOCKED, 429
       c. NS/IP window hit? → SET RL_IP_BLOCKED, 429

Degrades gracefully to non-atomic counting when Redis is unavailable.

_NAMESPACE is settings.POD_NAMESPACE, resolved once at startup:
  - K8s: start.sh reads the k8s namespace from the Downward API env var
    or the service-account namespace file, writes it to .env as POD_NAMESPACE.
  - Bare-metal / VM / docker-compose: defaults to the machine hostname
    (socket.gethostbyname_ex result computed in settings.py).
Since a deployment serves exactly one tenant, this is a startup constant —
no per-request lookup is needed or correct.
"""

import hashlib
import logging
import re
import time
from datetime import date

from sapl import settings
from django.core.cache import caches
from django.http import HttpResponse

logger = logging.getLogger('sapl.ratelimit')

# ---------------------------------------------------------------------------
# Tenant namespace — resolved once at startup from settings.POD_NAMESPACE.
# On K8s: the k8s namespace (e.g. "sapl31demo-df"), set by start.sh.
# On bare-metal / VM / docker-compose: the machine hostname (default).
# ---------------------------------------------------------------------------

_NAMESPACE = settings.POD_NAMESPACE

# ---------------------------------------------------------------------------
# Redis key templates — module-level constants, never inline strings
# ---------------------------------------------------------------------------

RL_IP_REQUESTS = 'rl:ip:{ip}:reqs'
RL_IP_BLOCKED = 'rl:ip:{ip}:blocked'
RL_IP_404S = 'rl:ip:{ip}:404s'
RL_USER_REQUESTS = 'rl:{ns}:user:{uid}:reqs'
RL_USER_BLOCKED = 'rl:{ns}:user:{uid}:blocked'
RL_NS_WINDOW = 'rl:{ns}:ip:{ip}:w:{bucket}'
RL_PATH_REQUESTS = 'rl:{ns}:path:{sha256}:reqs'
RL_UA_BLOCKLIST = 'rl:bot:ua:blocked'  # permanent SET — runtime UA deny list
RL_IP_PREFIX_BLOCKLIST = 'rl:ip_prefix:blocked'  # permanent SET — runtime IP-prefix deny list
RL_METRICS_BLOCKED = 'rl:metrics:{ns}:{date}'  # HASH: field = reason, value = daily count

# ZSET indexes — members are full block-key strings, score = expiry unix timestamp.
# Lets admin/monitoring tools enumerate active blocks with a single ZRANGEBYSCORE
# without scanning all keys. Prunable via: ZREMRANGEBYSCORE <index> 0 <now>.
RL_INDEX_BLOCKED_IPS = 'rl:index:blocked_ips'
RL_INDEX_BLOCKED_USERS = 'rl:index:blocked_users'

# API-specific rate limit keys — scope limited to /api/, never written by non-/api/ paths.
RL_API_IP_REQUESTS = 'rl:api:ns:{ns}:ip:{ip}:reqs'
RL_API_IP_BLOCKED = 'rl:api:ns:{ns}:ip:{ip}:blocked'
RL_INDEX_API_BLOCKED_IPS = 'rl:index:api_blocked_ips'

# ---------------------------------------------------------------------------
# API quota keys — per-tenant HASH, one key per period.
# Structure: HASH key = api_quota:{ns}:daily:{date}  field = {ip}  value = counter
#            HASH key = api_quota:{ns}:weekly:{week}  field = {ip}  value = counter
# Weekly key uses ISO week notation (yyyy-Www) — unambiguous, Monday-anchored.
# TTL set once on hash creation (Lua TTL guard); resets are implicit in the
# date/week embedded in the key name.  Fields are IPs; no per-field TTL.
# Memory: ~63 bytes/field vs ~148 bytes for per-IP STRING keys (~57% saving).
# ---------------------------------------------------------------------------
API_QUOTA_DAILY_HASH = 'api_quota:{ns}:daily:{date}'
API_QUOTA_WEEKLY_HASH = 'api_quota:{ns}:weekly:{week}'

# ---------------------------------------------------------------------------
# Bot UA fragments
# ---------------------------------------------------------------------------

BOT_UA_FRAGMENTS = [
    'GPTBot',
    'ClaudeBot',
    'PerplexityBot',
    'Bytespider',
    'AhrefsBot',
    'meta-externalagent',
    'OAI-SearchBot',
    'bingbot',
    'SERankingBacklinksBot',
    'Chrome/98.0.4758',  # known scraper impersonating an old Chrome
    'quiltbot',
    'AwarioBot',
]

_INCR_LUA = """
    local n = redis.call('INCR', KEYS[1])
    if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
    return n
"""

# Atomically increment a HASH field and set TTL on the hash key the first time
# it is created (TTL < 0 covers both -1 = no expire and -2 = key just created).
# KEYS[1] = hash key  ARGV[1] = field (IP)  ARGV[2] = TTL seconds
_HINCRBY_LUA = """
    local n = redis.call('HINCRBY', KEYS[1], ARGV[1], 1)
    if redis.call('TTL', KEYS[1]) < 0 then
        redis.call('EXPIRE', KEYS[1], ARGV[2])
    end
    return n
"""

# Atomically write a block key and record it in the sharded ZSET index.
# Prunes expired entries from the target shard before inserting the new one,
# keeping each shard bounded to only active blocks (amortised O(1) cleanup).
# KEYS[1] = block key  KEYS[2] = shard index key
# ARGV[1] = ttl (seconds)  ARGV[2] = expiry unix timestamp (now + ttl)
# ARGV[3] = current unix timestamp (for pruning: remove score < now)
_BLOCK_LUA = """
    local now = tonumber(ARGV[3])
    redis.call('SET',              KEYS[1], '1', 'EX', ARGV[1])
    redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', now - 1)
    redis.call('ZADD',             KEYS[2], ARGV[2], KEYS[1])
    return 1
"""


def _index_shard(ip, index_base):
    """
    Return the sharded ZSET key for an IP.

    IPs are distributed across RATE_LIMITER_INDEX_SHARDS shards using
    md5(ip) % N, spreading write contention and bounding each shard's size.
    The mapping is deterministic: the same IP always routes to the same shard.
    """
    n = settings.RATE_LIMITER_INDEX_SHARDS
    shard = int(hashlib.md5(ip.encode()).hexdigest(), 16) % n
    return f'{index_base}:{shard}'


def make_ratelimit_cache_key(key, key_prefix, version):
    """
    Pass-through cache key function for the 'ratelimit' Django cache backend.

    Django's default key function produces '{KEY_PREFIX}:{VERSION}:{key}',
    which turns django-ratelimit's own keys (already prefixed 'rl:{hash}')
    into ':1:rl:{hash}' — an ugly leading colon and version number that does
    not match the clean 'rl:*' keys written directly by RateLimitMiddleware.

    Setting KEY_FUNCTION to this function makes both key namespaces consistent:
    django-ratelimit decorator keys  →  rl:{hash}
    RateLimitMiddleware keys         →  rl:ip:{ip}:reqs  /  rl:{ns}:user:{uid}:reqs  / …
    """
    return key


def _sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()


def get_client_ip(request):
    """
    Return the real client IP, applying django-ratelimit's ip_mask so that
    IPv6 /64 subnets are collapsed to a single key (prevents per-address
    rotation attacks). Also checks HTTP_X_REAL_IP for nginx setups that
    use that header instead of X-Forwarded-For.

    Canonical source — imported from here by other SAPL modules.
    """
    from ratelimit.core import ip_mask
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = (
                request.META.get('HTTP_X_REAL_IP')
                or request.META.get('REMOTE_ADDR')
                or '0.0.0.0'
        )
    return ip_mask(ip)


def ratelimit_ip(group, request):
    """Key function for django-ratelimit decorators (group param is ignored)."""
    return get_client_ip(request)


def smart_key(group, request):
    """
    Auth-aware key for @ratelimit decorators.

    Authenticated users are keyed by user pk so that office workers sharing
    a NAT IP don't count against each other.  Anonymous requests fall back to
    the masked IP (IPv6 /64 collapsed via ip_mask).
    """
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        return str(user.pk)
    return ratelimit_ip(group, request)


def smart_rate(group, request):
    """
    Auth-aware rate string for @ratelimit decorators.

    Returns RATE_LIMITER_RATE_AUTHENTICATED for authenticated users,
    RATE_LIMITER_RATE for anonymous users — mirrors the thresholds applied
    by RateLimitMiddleware so view-level and middleware-level limits agree.
    """
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        return settings.RATE_LIMITER_RATE_AUTHENTICATED
    return settings.RATE_LIMITER_RATE


def _is_same_origin(request):
    """
    Return True if Origin or Referer header matches the current SAPL host.
    Strips port and lowercases both sides before comparing — DNS is case-insensitive
    and reverse proxies may expose a different port than the browser sees.
    Checks Origin first; falls back to Referer only when Origin is absent.
    Returns False when both headers are absent.
    """
    from urllib.parse import urlparse

    def _normalize(host):
        return host.lower().split(':', 1)[0].strip()

    try:
        host = _normalize(request.get_host())
    except Exception:
        return False

    origin = request.META.get('HTTP_ORIGIN', '')
    if origin:
        try:
            return _normalize(urlparse(origin).netloc) == host
        except ValueError:
            return False

    referer = request.META.get('HTTP_REFERER', '')
    if referer:
        try:
            return _normalize(urlparse(referer).netloc) == host
        except ValueError:
            return False

    return False


def _is_suspicious_headers(request):
    """Real browsers send Accept-Language + Accept; bots frequently omit them."""
    missing = sum([
        not request.META.get('HTTP_ACCEPT_LANGUAGE'),
        not request.META.get('HTTP_ACCEPT'),
    ])
    # Também considera User-Agent antes de bloquear
    has_ua = bool(request.META.get('HTTP_USER_AGENT'))
    return missing >= 2 and not has_ua


def _parse_rate(rate_str):
    """Parse '35/m' or '120/m' into (count, seconds)."""
    count, period = rate_str.split('/')
    count = int(count)
    seconds = {'s': 1, 'm': 60, 'h': 3600}.get(period.lower(), 60)
    return count, seconds


def _incr_with_ttl(key, ttl):
    """
    Atomic INCR + EXPIRE via Redis Lua script (ratelimit cache, DB 1).
    Falls back to non-atomic cache get/set when Redis is unavailable.
    Exported at module level so sapl.base.media can reuse it for path counters.
    """
    try:
        from django_redis import get_redis_connection
        client = get_redis_connection('ratelimit')
        return client.eval(_INCR_LUA, 1, key, ttl)
    except Exception:
        rl_cache = caches['ratelimit']
        count = (rl_cache.get(key) or 0) + 1
        rl_cache.set(key, count, timeout=ttl)
        return count


def _hincrby_with_ttl(hash_key, field, ttl):
    """
    Atomic HINCRBY + conditional EXPIRE via Redis Lua script (ratelimit cache, DB 1).

    Increments the counter for `field` inside `hash_key` and sets a TTL on the
    hash key if it does not already have one (i.e. on first creation).
    Falls back to a composite STRING key `hash_key:field` when Redis is unavailable.
    """
    try:
        from django_redis import get_redis_connection
        client = get_redis_connection('ratelimit')
        return client.eval(_HINCRBY_LUA, 1, hash_key, field, ttl)
    except Exception:
        rl_cache = caches['ratelimit']
        fallback_key = f'{hash_key}:{field}'
        count = (rl_cache.get(fallback_key) or 0) + 1
        rl_cache.set(fallback_key, count, timeout=ttl)
        return count


def _set_block(block_key, index_key, ttl):
    """
    Atomically set a block key (with TTL) and record it in a sharded ZSET index.
    Score = expiry unix timestamp.  Prunes expired entries from the target shard
    before inserting (inline cleanup — no separate maintenance job needed).
    Falls back to a plain cache.set when Redis is unavailable (index skipped).
    """
    now       = int(time.time())
    expire_at = now + ttl
    try:
        from django_redis import get_redis_connection
        client = get_redis_connection('ratelimit')
        client.eval(_BLOCK_LUA, 2, block_key, index_key, ttl, expire_at, now)
    except Exception:
        caches['ratelimit'].set(block_key, 1, timeout=ttl)


class RateLimitMiddleware:
    BLOCK_TTL = 300  # seconds an IP/user stays blocked after threshold breach

    # In-process cache for the Redis UA deny list.
    # Shared across all instances in the same worker process (one per worker).
    # Refreshed every RATE_LIMITER_UA_BLOCKLIST_REFRESH seconds via SMEMBERS.
    _ua_blocklist: set = set()
    _ua_blocklist_fetched_at: float = 0.0

    # In-process cache for the Redis IP-prefix deny list (operator-curated SET
    # of dotted-decimal prefixes). Normalized to trailing-dot form on refresh so
    # checking is O(1) per candidate via set membership.
    _ip_prefix_blocklist: set = set()
    _ip_prefix_blocklist_fetched_at: float = 0.0

    def __init__(self, get_response):
        self.get_response = get_response
        self.anon_threshold, self.anon_window = _parse_rate(settings.RATE_LIMITER_RATE)
        self.auth_threshold, self.auth_window = _parse_rate(settings.RATE_LIMITER_RATE_AUTHENTICATED)
        self._rl_cache = caches['ratelimit']
        self.not_found_threshold = settings.RATE_LIMIT_404_THRESHOLD
        self._bypass_paths = [
            re.compile(p) for p in getattr(settings, 'RATE_LIMIT_BYPASS_PATHS', [])
        ]
        self.api_quota_daily = settings.API_QUOTA_DAILY
        self.api_quota_weekly = settings.API_QUOTA_WEEKLY
        self.api_rate_limit_enabled = getattr(settings, 'API_RATE_LIMIT_ENABLED', True)
        self.api_threshold = getattr(settings, 'API_RATE_LIMIT_THRESHOLD', 60)
        self.api_window = getattr(settings, 'API_RATE_LIMIT_WINDOW_SECONDS', 60)
        self.api_block_seconds = getattr(settings, 'API_RATE_LIMIT_BLOCK_SECONDS', 300)
        self.api_same_origin_bypass = getattr(settings, 'API_RATE_LIMIT_SAME_ORIGIN_BYPASS', True)
        logger.info(
            '[RATELIMIT] anon=%s  auth=%s  bot=%s  bypass_paths=%s',
            settings.RATE_LIMITER_RATE,
            settings.RATE_LIMITER_RATE_AUTHENTICATED,
            settings.RATE_LIMITER_RATE_BOT,
            [p.pattern for p in self._bypass_paths] or '(none)',
        )
        logger.info(
            '[API QUOTAS] daily=%s weekly=%s  (all callers keyed by IP)',
            settings.API_QUOTA_DAILY,
            settings.API_QUOTA_WEEKLY,
        )
        logger.info(
            '[API RATE LIMIT] enabled=%s threshold=%s window=%ss block=%ss same_origin_bypass=%s',
            self.api_rate_limit_enabled, self.api_threshold, self.api_window,
            self.api_block_seconds, self.api_same_origin_bypass,
        )

    def __call__(self, request):
        if any(p.match(request.path) for p in self._bypass_paths):
            return self.get_response(request)

        # Reject parameter pollution: the `page` param must appear at most once.
        # Duplicate page= values (e.g. ?page=3&page=2&page=3) are a bot
        # fingerprint — no legitimate browser or script sends this.
        if len(request.GET.getlist('page')) > 1:
            logger.warning(
                'ratelimit_block layer=django reason=param_pollution ip=%s path=%s',
                get_client_ip(request), request.path,
            )
            self._inc_block_metric('param_pollution')
            response = HttpResponse(status=400)
            response['X-RateLimit-Reason'] = 'param_pollution'
            return response

        if request.path.startswith('/api/'):
            return self._handle_api(request)

        decision = self._evaluate(request)
        if decision['action'] == 'block':
            logger.warning(
                'ratelimit_block layer=django reason=%s ip=%s path=%s namespace=%s',
                decision['reason'],
                decision['ip'],
                request.path,
                _NAMESPACE,
                extra={'ua': request.META.get('HTTP_USER_AGENT', '')},
            )
            self._inc_block_metric(decision['reason'])
            if decision['reason'] == 'ip_prefix_blocked':
                response = HttpResponse(status=403)
            else:
                response = HttpResponse(status=429)
                response['Retry-After'] = self.BLOCK_TTL
            response['X-RateLimit-Reason'] = decision['reason']
            return response
        logger.debug(
            'ratelimit_pass ip=%s path=%s user=%s namespace=%s',
            decision['ip'],
            request.path,
            getattr(getattr(request, 'user', None), 'pk', 'anon'),
            _NAMESPACE,
        )
        response = self.get_response(request)
        if response.status_code == 404:
            self._handle_not_found(request, decision['ip'])
        return response

    # ------------------------------------------------------------------
    # /api/ handling
    # ------------------------------------------------------------------

    def _api_block_response(self, reason, retry_after=None):
        from django.http import JsonResponse
        if reason == 'ip_prefix_blocked':
            resp = JsonResponse({'detail': 'Forbidden.'}, status=403)
            resp['X-RateLimit-Reason'] = reason
            return resp
        if retry_after is None:
            retry_after = self.api_block_seconds
        resp = JsonResponse(
            {'detail': 'API rate limit exceeded. Please reduce polling frequency.',
             'retry_after_seconds': retry_after},
            status=429,
        )
        resp['Retry-After'] = retry_after
        resp['X-RateLimit-Reason'] = reason
        return resp

    def _handle_api(self, request):
        # 1. OPTIONS preflight — CORS must never be blocked
        if request.method == 'OPTIONS':
            return self.get_response(request)

        ip = get_client_ip(request)

        # 2. IP-prefix block — operator-curated deny list, applies to everyone.
        #    Block checks (2-4) must run before the same-origin bypass below:
        #    Origin/Referer are client-controlled and trivially spoofable, so
        #    they must never be able to override an already-made block decision.
        if self._is_ip_prefix_blocked(ip):
            logger.warning(
                'api_rate_limit_block reason=ip_prefix_blocked ip=%s path=%s user_agent=%s',
                ip, request.path, request.META.get('HTTP_USER_AGENT', ''),
            )
            self._inc_block_metric('api_ip_prefix_blocked')
            return self._api_block_response('ip_prefix_blocked')

        # 3. Global IP block also covers /api/
        if self._rl_cache.get(RL_IP_BLOCKED.format(ip=ip)):
            logger.warning(
                'api_rate_limit_block reason=global_ip_blocked ip=%s path=%s user_agent=%s',
                ip, request.path, request.META.get('HTTP_USER_AGENT', ''),
            )
            self._inc_block_metric('api_global_ip_blocked')
            return self._api_block_response('global_ip_blocked')

        # 4. API-specific block (blocks /api/ only, never set by non-/api/ paths)
        if self._rl_cache.get(RL_API_IP_BLOCKED.format(ns=_NAMESPACE, ip=ip)):
            logger.warning(
                'api_rate_limit_block reason=api_ip_blocked ip=%s path=%s user_agent=%s',
                ip, request.path, request.META.get('HTTP_USER_AGENT', ''),
            )
            self._inc_block_metric('api_ip_blocked')
            return self._api_block_response('api_ip_blocked')

        # 5. Same-origin (SAPL's own polling) — exempt from quota/rate-limit
        #    accounting only (steps 6-7 below). Must come after the block
        #    checks above, never before them.
        if self.api_same_origin_bypass and _is_same_origin(request):
            return self.get_response(request)

        # 6. Daily/weekly quota (existing logic, preserved)
        exceeded = self._check_api_quota(request)
        if exceeded:
            logger.warning(
                'quota_exceeded window=%s ip=%s path=%s namespace=%s',
                exceeded, ip, request.path, _NAMESPACE,
                extra={'ua': request.META.get('HTTP_USER_AGENT', '')},
            )
            self._inc_block_metric(f'quota_{exceeded}')
            response = HttpResponse(status=429)
            response['Retry-After'] = 86400
            response['X-RateLimit-Reason'] = f'quota_{exceeded}'
            return response

        # 7. Per-minute rate limit — 60/min for all callers (anon and auth).
        #    Auth is not exempt: authenticating must not bypass this cap.
        #    Writes rl:api:ip:<ip>:blocked only — never rl:ip:<ip>:blocked.
        if self.api_rate_limit_enabled:
            count = self._incr_with_ttl(RL_API_IP_REQUESTS.format(ns=_NAMESPACE, ip=ip), self.api_window)
            if count >= self.api_threshold:
                _set_block(RL_API_IP_BLOCKED.format(ns=_NAMESPACE, ip=ip), _index_shard(ip, RL_INDEX_API_BLOCKED_IPS), self.api_block_seconds)
                logger.warning(
                    'api_rate_limit_block reason=api_threshold_exceeded '
                    'ip=%s path=%s user_agent=%s count=%s threshold=%s',
                    ip, request.path, request.META.get('HTTP_USER_AGENT', ''),
                    count, self.api_threshold,
                )
                self._inc_block_metric('api_threshold_exceeded')
                return self._api_block_response('api_threshold_exceeded')
        return self.get_response(request)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def _evaluate(self, request):
        ip = get_client_ip(request)

        # Check 0: IP-prefix block — operator-curated deny list, applies to everyone
        if self._is_ip_prefix_blocked(ip):
            return {'action': 'block', 'reason': 'ip_prefix_blocked', 'ip': ip}

        # Check 1: known bad UA (hardcoded Python list — substring match)
        ua = request.META.get('HTTP_USER_AGENT', '')
        for fragment in BOT_UA_FRAGMENTS:
            if fragment.lower() in ua.lower():
                return {'action': 'block', 'reason': 'known_ua', 'ip': ip}

        # Check 1b: runtime UA deny list (Redis SET — token hash match)
        if self._is_redis_blocked_ua(ua):
            return {'action': 'block', 'reason': 'redis_ua', 'ip': ip}

        # Check 2: IP already blocked — authenticated users are exempt since they
        # have independent per-user limiting at check 3c; IP blocks target anonymous traffic.
        user = getattr(request, 'user', None)
        if not (user and user.is_authenticated) and self._rl_cache.get(RL_IP_BLOCKED.format(ip=ip)):
            return {'action': 'block', 'reason': 'ip_blocked', 'ip': ip}

        if user is not None and user.is_authenticated:
            return self._evaluate_authenticated(request, ip)
        return self._evaluate_anonymous(request, ip)

    def _evaluate_authenticated(self, request, ip):
        uid = str(request.user.pk)

        # Check 3a: user already blocked
        if self._rl_cache.get(RL_USER_BLOCKED.format(ns=_NAMESPACE, uid=uid)):
            return {'action': 'block', 'reason': 'user_blocked', 'ip': ip}

        # Check 3b: suspicious headers
        if _is_suspicious_headers(request):
            return {'action': 'block', 'reason': 'suspicious_headers_auth', 'ip': ip}

        # Check 3c: authenticated request rate — return 429 for this request only;
        # no persistent block key so the window resets naturally after auth_window
        # seconds. A 300s lockout is wrong for a logged-in user who clicked fast.
        count = self._incr_with_ttl(
            RL_USER_REQUESTS.format(ns=_NAMESPACE, uid=uid), ttl=self.auth_window
        )
        if count >= self.auth_threshold:
            return {'action': 'block', 'reason': 'auth_user_rate', 'ip': ip}

        return {'action': 'pass', 'ip': ip}

    def _evaluate_anonymous(self, request, ip):
        # Check 4a: suspicious headers
        if _is_suspicious_headers(request):
            return {'action': 'block', 'reason': 'suspicious_headers', 'ip': ip}

        # Check 4b: IP request rate
        count = self._incr_with_ttl(RL_IP_REQUESTS.format(ip=ip), ttl=self.anon_window)
        if count >= self.anon_threshold:
            _set_block(RL_IP_BLOCKED.format(ip=ip), _index_shard(ip, RL_INDEX_BLOCKED_IPS), self.BLOCK_TTL)
            return {'action': 'block', 'reason': 'ip_rate', 'ip': ip}

        # Check 4c: per-namespace/IP/window (catches UA rotators behind NAT)
        bucket = int(time.time() // self.anon_window)
        count = self._incr_with_ttl(
            RL_NS_WINDOW.format(ns=_NAMESPACE, ip=ip, bucket=bucket),
            ttl=self.anon_window * 2,
        )
        if count >= self.anon_threshold:
            _set_block(RL_IP_BLOCKED.format(ip=ip), _index_shard(ip, RL_INDEX_BLOCKED_IPS), self.BLOCK_TTL)
            return {'action': 'block', 'reason': 'ua_rotation', 'ip': ip}

        return {'action': 'pass', 'ip': ip}

    # ------------------------------------------------------------------
    # Helpers — delegate to module-level so media.py can reuse them
    # ------------------------------------------------------------------

    def _handle_not_found(self, request, ip):
        """
        Block IPs that accumulate too many 404s in one window — catches scanner
        probes that use paths without recognised extensions (e.g. /wp-login,
        /.git/HEAD, /xmlrpc) and bypass check 2b entirely.
        Only anonymous requests are counted; authenticated users have their own
        per-user rate limit and may legitimately hit stale bookmarks.
        """
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return
        count = self._incr_with_ttl(RL_IP_404S.format(ip=ip), ttl=self.anon_window)
        if count >= self.not_found_threshold:
            _set_block(RL_IP_BLOCKED.format(ip=ip), _index_shard(ip, RL_INDEX_BLOCKED_IPS), self.BLOCK_TTL)
            logger.warning(
                'ratelimit_block layer=django reason=404_scan ip=%s path=%s namespace=%s',
                ip, request.path, _NAMESPACE,
                extra={'ua': request.META.get('HTTP_USER_AGENT', '')},
            )
            self._inc_block_metric('404_scan')

    def _check_api_quota(self, request):
        """
        Increment daily and weekly API quota counters for all /api/ callers.
        All callers are keyed by IP — auth status is not checked.

        Keys are HASH structures: one hash per tenant per period, field = IP.
        This keeps the global keyspace at O(tenants) instead of O(unique IPs),
        reducing Redis memory ~57% vs. per-IP STRING keys at scale.

        Fails open (returns None) if Redis/cache is unavailable.
        """
        today = date.today()
        iso = today.isocalendar()
        date_str = today.isoformat()
        week_str = f'{iso[0]}-W{iso[1]:02d}'

        ip = get_client_ip(request)
        api_d_hash = API_QUOTA_DAILY_HASH.format(ns=_NAMESPACE, date=date_str)
        api_w_hash = API_QUOTA_WEEKLY_HASH.format(ns=_NAMESPACE, week=week_str)

        try:
            if _hincrby_with_ttl(api_d_hash, ip, 86400) > self.api_quota_daily:
                return 'daily'
            if _hincrby_with_ttl(api_w_hash, ip, 7 * 86400) > self.api_quota_weekly:
                return 'weekly'
        except Exception:
            pass  # fail open — quota not enforced when Redis unavailable
        return None

    def _incr_with_ttl(self, key, ttl):
        return _incr_with_ttl(key, ttl)

    def _inc_block_metric(self, reason):
        """Increment daily per-reason block counter in Redis DB 1 (TTL 8 days)."""
        hash_key = RL_METRICS_BLOCKED.format(ns=_NAMESPACE, date=date.today().isoformat())
        try:
            _hincrby_with_ttl(hash_key, reason, ttl=8 * 86400)
        except Exception:
            pass

    def _refresh_ua_blocklist(self):
        """
        Fetch the full UA deny list from Redis DB 1 (SMEMBERS).
        Stores sha256 hex-strings in the class-level set.
        Falls back silently — an empty set means no runtime blocks.
        """
        try:
            from django_redis import get_redis_connection
            client = get_redis_connection('ratelimit')
            raw = client.smembers(RL_UA_BLOCKLIST)
            RateLimitMiddleware._ua_blocklist = {
                m.decode() if isinstance(m, bytes) else m for m in raw
            }
            RateLimitMiddleware._ua_blocklist_fetched_at = time.time()
            logger.debug('[RATELIMIT] ua_blocklist refreshed  entries=%d', len(raw))
        except Exception as exc:
            logger.debug('[RATELIMIT] ua_blocklist refresh skipped: %s', exc)

    def _is_redis_blocked_ua(self, ua):
        """
        Return True if any slash/space/semicolon token in `ua` has a sha256
        that appears in the Redis UA deny list.

        The SET stores sha256(fragment) — e.g. sha256('GPTBot').
        Tokenising by common UA separators means 'GPTBot/1.1 (OpenAI)'
        produces token 'GPTBot' whose hash matches the seeded entry.
        Degrades to False when Redis is unavailable.
        """
        if time.time() - self._ua_blocklist_fetched_at > settings.RATE_LIMITER_UA_BLOCKLIST_REFRESH:
            self._refresh_ua_blocklist()
        if not self._ua_blocklist:
            return False
        tokens = re.split(r'[\s/;()+,]+', ua)
        return any(
            hashlib.sha256(t.encode()).hexdigest() in self._ua_blocklist
            for t in tokens if t
        )

    def _refresh_ip_prefix_blocklist(self):
        """
        Fetch the full IP-prefix deny list from Redis DB 1 (SMEMBERS) and
        normalise entries to trailing-dot form so membership checks are O(1).

        Normalisation: strip trailing dot, then re-add if fewer than 3 dots
        (i.e. it's a prefix, not a full dotted-quad). Examples:
          '103.124.225'  → '103.124.225.'
          '103.124.225.' → '103.124.225.'
          '103.124.225.7'→ '103.124.225.7'  (exact IP, no trailing dot)
        """
        try:
            from django_redis import get_redis_connection
            client = get_redis_connection('ratelimit')
            raw = client.smembers(RL_IP_PREFIX_BLOCKLIST)
            normalized = set()
            for m in raw:
                entry = m.decode() if isinstance(m, bytes) else m
                stripped = entry.rstrip('.')
                normalized.add(stripped + '.' if stripped.count('.') < 3 else stripped)
            RateLimitMiddleware._ip_prefix_blocklist = normalized
            RateLimitMiddleware._ip_prefix_blocklist_fetched_at = time.time()
            logger.debug('[RATELIMIT] ip_prefix_blocklist refreshed  entries=%d', len(normalized))
        except Exception as exc:
            logger.debug('[RATELIMIT] ip_prefix_blocklist refresh skipped: %s', exc)

    def _is_ip_prefix_blocked(self, ip):
        """
        Return True if `ip` or any of its dot-anchored prefixes is in the
        local IP-prefix deny set.

        Generates up to 4 candidates for '203.0.113.42':
          '203.', '203.0.', '203.0.113.', '203.0.113.42'
        Each lookup is O(1) against the normalised in-process set.
        Degrades to False when Redis is unavailable (empty set).
        """
        if time.time() - self._ip_prefix_blocklist_fetched_at > settings.RATE_LIMITER_IP_PREFIX_BLOCKLIST_REFRESH:
            self._refresh_ip_prefix_blocklist()
        if not self._ip_prefix_blocklist:
            return False
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        candidates = (
            parts[0] + '.',
            parts[0] + '.' + parts[1] + '.',
            parts[0] + '.' + parts[1] + '.' + parts[2] + '.',
            ip,
        )
        return any(c in self._ip_prefix_blocklist for c in candidates)
