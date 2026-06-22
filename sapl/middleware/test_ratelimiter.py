"""
Unit tests for sapl/middleware/ratelimit.py.

No database access is needed — all tests use RequestFactory and mocks.
Redis is never contacted; _incr_with_ttl is either mocked directly on the
middleware instance or the fallback non-atomic path is exercised via the
mock cache.
"""

import time

import pytest
from unittest.mock import MagicMock, patch
from django.test import RequestFactory

from sapl.middleware.ratelimit import (
    _NAMESPACE,
    _hincrby_with_ttl,
    _index_shard,
    _is_same_origin,
    _is_suspicious_headers,
    _parse_rate,
    get_client_ip,
    make_ratelimit_cache_key,
    API_QUOTA_DAILY_HASH,
    API_QUOTA_WEEKLY_HASH,
    RateLimitMiddleware,
    RL_API_IP_BLOCKED,
    RL_API_IP_REQUESTS,
    RL_INDEX_BLOCKED_IPS,
    RL_IP_BLOCKED,
    RL_IP_PREFIX_BLOCKLIST,
    RL_USER_BLOCKED,
    smart_key,
    smart_rate,
)

# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------

_factory = RequestFactory()

# Headers that a normal browser would send — used as the default baseline.
_NORMAL_HEADERS = {
    'HTTP_ACCEPT': 'text/html,application/xhtml+xml',
    'HTTP_ACCEPT_LANGUAGE': 'pt-BR,pt;q=0.9',
}


def _req(ip='1.2.3.4', ua='Mozilla/5.0', path='/', extra_meta=None):
    """GET request with sensible defaults and browser-like headers."""
    request = _factory.get(path)
    request.META.update({'REMOTE_ADDR': ip, 'HTTP_USER_AGENT': ua, **_NORMAL_HEADERS})
    if extra_meta:
        request.META.update(extra_meta)
    return request


def _anon_req(**kwargs):
    r = _req(**kwargs)
    r.user = MagicMock(is_authenticated=False)
    return r


def _auth_req(uid=7, **kwargs):
    r = _req(**kwargs)
    r.user = MagicMock(is_authenticated=True, pk=uid)
    return r


def _make_middleware(
    anon_rate='35/m',
    auth_rate='120/m',
    api_rate_limit_enabled=True,
    api_threshold=60,
    api_window=60,
    api_block_seconds=300,
    api_same_origin_bypass=True,
):
    """
    Return (middleware, mock_cache).

    The ratelimit cache is replaced with a MagicMock whose .get() returns None
    by default (nothing blocked, no counters set).  Tests may replace
    mock_cache.get.side_effect or mock mw._incr_with_ttl directly.

    sapl.middleware.ratelimit imports settings as `from sapl import settings`
    (a direct module reference), so django.test.override_settings has no effect
    on it.  We patch the name in the ratelimit module's namespace instead.
    """
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    get_response = MagicMock(return_value=MagicMock(status_code=200))

    mock_settings = MagicMock()
    mock_settings.RATE_LIMITER_RATE = anon_rate
    mock_settings.RATE_LIMITER_RATE_AUTHENTICATED = auth_rate
    mock_settings.RATE_LIMITER_RATE_BOT = '5/m'
    mock_settings.RATE_LIMIT_404_THRESHOLD = 20
    mock_settings.RATE_LIMIT_BYPASS_PATHS = []
    mock_settings.POD_NAMESPACE = _NAMESPACE  # keep module-level _NAMESPACE consistent
    mock_settings.API_QUOTA_DAILY = 999999
    mock_settings.API_QUOTA_WEEKLY = 999999
    mock_settings.RATE_LIMITER_UA_BLOCKLIST_REFRESH = 60
    mock_settings.RATE_LIMITER_IP_PREFIX_BLOCKLIST_REFRESH = 60
    mock_settings.API_RATE_LIMIT_ENABLED = api_rate_limit_enabled
    mock_settings.API_RATE_LIMIT_THRESHOLD = api_threshold
    mock_settings.API_RATE_LIMIT_WINDOW_SECONDS = api_window
    mock_settings.API_RATE_LIMIT_BLOCK_SECONDS = api_block_seconds
    mock_settings.API_RATE_LIMIT_SAME_ORIGIN_BYPASS = api_same_origin_bypass
    mock_settings.RATE_LIMITER_INDEX_SHARDS = 3

    with (
        patch('sapl.middleware.ratelimit.caches') as mock_caches,
        patch('sapl.middleware.ratelimit.settings', mock_settings),
    ):
        mock_caches.__getitem__.return_value = mock_cache
        mw = RateLimitMiddleware(get_response)
        # __init__ already set mw._rl_cache = caches['ratelimit'] == mock_cache,
        # but reassign explicitly so tests have a direct handle on the same object.
        mw._rl_cache = mock_cache
    return mw, mock_cache


# ---------------------------------------------------------------------------
# _parse_rate
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('rate_str,expected', [
    ('35/m', (35, 60)),
    ('120/m', (120, 60)),
    ('10/s', (10, 1)),
    ('5/h', (5, 3600)),
    ('1/M', (1, 60)),   # period is case-insensitive
])
def test_parse_rate(rate_str, expected):
    assert _parse_rate(rate_str) == expected


# ---------------------------------------------------------------------------
# make_ratelimit_cache_key — pass-through, no mangling
# ---------------------------------------------------------------------------

def test_make_ratelimit_cache_key_passthrough():
    assert make_ratelimit_cache_key('rl:ip:1.2.3.4:reqs', 'some_prefix', 1) == 'rl:ip:1.2.3.4:reqs'
    assert make_ratelimit_cache_key('rl:abc123', '', 99) == 'rl:abc123'


# ---------------------------------------------------------------------------
# _is_suspicious_headers
# ---------------------------------------------------------------------------

def test_suspicious_both_headers_missing():
    r = _factory.get('/')
    r.META.pop('HTTP_ACCEPT', None)
    r.META.pop('HTTP_ACCEPT_LANGUAGE', None)
    assert _is_suspicious_headers(r) is True


def test_suspicious_one_header_missing_is_not_suspicious():
    """Only flagged when *both* headers are absent."""
    r = _factory.get('/')
    r.META['HTTP_ACCEPT'] = 'text/html'
    r.META.pop('HTTP_ACCEPT_LANGUAGE', None)
    assert _is_suspicious_headers(r) is False


def test_suspicious_both_headers_present():
    r = _factory.get('/')
    r.META['HTTP_ACCEPT'] = 'text/html'
    r.META['HTTP_ACCEPT_LANGUAGE'] = 'pt-BR'
    assert _is_suspicious_headers(r) is False


# ---------------------------------------------------------------------------
# get_client_ip — header priority and XFF chain
# ---------------------------------------------------------------------------

def test_get_client_ip_remote_addr():
    r = _factory.get('/')
    r.META['REMOTE_ADDR'] = '10.0.0.1'
    assert get_client_ip(r) == '10.0.0.1'


def test_get_client_ip_xff_single():
    r = _factory.get('/')
    r.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.5'
    assert get_client_ip(r) == '203.0.113.5'


def test_get_client_ip_xff_chain_uses_leftmost():
    """The leftmost IP in XFF is the real client; the rest are proxies."""
    r = _factory.get('/')
    r.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.5, 10.0.0.1, 10.0.0.2'
    assert get_client_ip(r) == '203.0.113.5'


def test_get_client_ip_x_real_ip_used_when_no_xff():
    r = _factory.get('/')
    r.META['REMOTE_ADDR'] = '127.0.0.1'
    r.META['HTTP_X_REAL_IP'] = '203.0.113.9'
    assert get_client_ip(r) == '203.0.113.9'


def test_get_client_ip_xff_preferred_over_x_real_ip():
    r = _factory.get('/')
    r.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1'
    r.META['HTTP_X_REAL_IP'] = '203.0.113.2'
    assert get_client_ip(r) == '203.0.113.1'


# ---------------------------------------------------------------------------
# smart_key / smart_rate
# ---------------------------------------------------------------------------

def test_smart_key_anon_returns_masked_ip():
    r = _anon_req(ip='5.5.5.5')
    assert smart_key(None, r) == '5.5.5.5'


def test_smart_key_auth_returns_pk_string():
    r = _auth_req(uid=42, ip='5.5.5.5')
    assert smart_key(None, r) == '42'


def test_smart_rate_anon_returns_anon_rate():
    with patch('sapl.middleware.ratelimit.settings') as mock_s:
        mock_s.RATE_LIMITER_RATE = '35/m'
        mock_s.RATE_LIMITER_RATE_AUTHENTICATED = '120/m'
        assert smart_rate(None, _anon_req()) == '35/m'


def test_smart_rate_auth_returns_auth_rate():
    with patch('sapl.middleware.ratelimit.settings') as mock_s:
        mock_s.RATE_LIMITER_RATE = '35/m'
        mock_s.RATE_LIMITER_RATE_AUTHENTICATED = '120/m'
        assert smart_rate(None, _auth_req()) == '120/m'


# ---------------------------------------------------------------------------
# _index_shard — sharded ZSET key routing
# ---------------------------------------------------------------------------

def test_index_shard_is_deterministic():
    """Same IP always maps to the same shard."""
    from sapl.middleware.ratelimit import _index_shard
    with patch('sapl.middleware.ratelimit.settings') as mock_s:
        mock_s.RATE_LIMITER_INDEX_SHARDS = 3
        key1 = _index_shard('1.2.3.4', 'rl:index:blocked_ips')
        key2 = _index_shard('1.2.3.4', 'rl:index:blocked_ips')
        assert key1 == key2


def test_index_shard_stays_within_range():
    """Shard suffix is always 0 … N-1."""
    from sapl.middleware.ratelimit import _index_shard
    import re
    with patch('sapl.middleware.ratelimit.settings') as mock_s:
        mock_s.RATE_LIMITER_INDEX_SHARDS = 3
        ips = [f'10.0.0.{i}' for i in range(50)]
        for ip in ips:
            key = _index_shard(ip, 'rl:index:blocked_ips')
            m = re.search(r':(\d+)$', key)
            assert m and 0 <= int(m.group(1)) < 3, f'out-of-range shard for {ip}: {key}'


def test_index_shard_distributes_across_shards():
    """With enough IPs, all 3 shards are used."""
    from sapl.middleware.ratelimit import _index_shard
    with patch('sapl.middleware.ratelimit.settings') as mock_s:
        mock_s.RATE_LIMITER_INDEX_SHARDS = 3
        shards_seen = {
            _index_shard(f'192.168.{i}.{j}', 'rl:index:blocked_ips').split(':')[-1]
            for i in range(5) for j in range(10)
        }
        assert shards_seen == {'0', '1', '2'}


# ---------------------------------------------------------------------------
# Check 0 — IP-prefix blocklist (operator-curated SET, dot-anchored matching)
# ---------------------------------------------------------------------------

@pytest.fixture
def _seed_prefix_blocklist():
    """
    Seed RateLimitMiddleware._ip_prefix_blocklist for the test and restore the
    previous class-level state afterwards (it's shared across instances, like
    the UA blocklist).
    """
    saved_list = RateLimitMiddleware._ip_prefix_blocklist
    saved_fetched_at = RateLimitMiddleware._ip_prefix_blocklist_fetched_at

    def _seed(prefixes):
        RateLimitMiddleware._ip_prefix_blocklist = set(prefixes)
        RateLimitMiddleware._ip_prefix_blocklist_fetched_at = time.time()

    yield _seed

    RateLimitMiddleware._ip_prefix_blocklist = saved_list
    RateLimitMiddleware._ip_prefix_blocklist_fetched_at = saved_fetched_at


def test_is_ip_prefix_blocked_matches_dot_boundary(_seed_prefix_blocklist):
    mw, _ = _make_middleware()
    _seed_prefix_blocklist(['103.124.225'])
    assert mw._is_ip_prefix_blocked('103.124.225.7') is True
    # must not match on raw substring — only on a full-octet boundary
    assert mw._is_ip_prefix_blocked('103.124.2250.1') is False
    assert mw._is_ip_prefix_blocked('103.124.2255') is False


def test_is_ip_prefix_blocked_exact_match(_seed_prefix_blocklist):
    mw, _ = _make_middleware()
    _seed_prefix_blocklist(['103.124.225'])
    assert mw._is_ip_prefix_blocked('103.124.225') is True


def test_is_ip_prefix_blocked_full_address_matches_only_exactly(_seed_prefix_blocklist):
    mw, _ = _make_middleware()
    _seed_prefix_blocklist(['103.124.225.7'])
    assert mw._is_ip_prefix_blocked('103.124.225.7') is True
    # a full dotted-quad entry must not be treated as a prefix of a longer string
    assert mw._is_ip_prefix_blocked('103.124.225.70') is False


def test_is_ip_prefix_blocked_trailing_dot_in_stored_prefix(_seed_prefix_blocklist):
    mw, _ = _make_middleware()
    _seed_prefix_blocklist(['103.124.225.'])
    # anchoring must not double the dot ('103.124.225..') and break the match
    assert mw._is_ip_prefix_blocked('103.124.225.7') is True


def test_is_ip_prefix_blocked_empty_list_passes(_seed_prefix_blocklist):
    mw, _ = _make_middleware()
    _seed_prefix_blocklist([])
    assert mw._is_ip_prefix_blocked('1.2.3.4') is False


def test_is_ip_prefix_blocked_no_match_passes(_seed_prefix_blocklist):
    mw, _ = _make_middleware()
    _seed_prefix_blocklist(['103.124.225', '45.177.154'])
    assert mw._is_ip_prefix_blocked('1.2.3.4') is False


def test_evaluate_blocks_on_ip_prefix_before_other_checks(_seed_prefix_blocklist):
    mw, _ = _make_middleware()
    _seed_prefix_blocklist(['1.2.3'])
    result = mw._evaluate(_anon_req(ip='1.2.3.4', ua='GPTBot'))
    # would otherwise match the known_ua check — prefix block must win
    assert result == {'action': 'block', 'reason': 'ip_prefix_blocked', 'ip': '1.2.3.4'}


def test_evaluate_passes_through_when_ip_not_in_prefix_list(_seed_prefix_blocklist):
    mw, _ = _make_middleware()
    _seed_prefix_blocklist(['9.9.9'])
    mw._incr_with_ttl = MagicMock(return_value=1)
    result = mw._evaluate(_anon_req(ip='1.2.3.4'))
    assert result['action'] == 'pass'


def test_refresh_ip_prefix_blocklist_populates_set(_seed_prefix_blocklist):
    mw, _ = _make_middleware()
    _seed_prefix_blocklist([])  # start empty so the refresh result is observable

    mock_client = MagicMock()
    mock_client.smembers.return_value = {b'103.124.225', b'45.177.154'}
    with patch('django_redis.get_redis_connection', return_value=mock_client):
        mw._refresh_ip_prefix_blocklist()

    mock_client.smembers.assert_called_once_with(RL_IP_PREFIX_BLOCKLIST)
    assert RateLimitMiddleware._ip_prefix_blocklist == {'103.124.225', '45.177.154'}


# ---------------------------------------------------------------------------
# Check 1 — known bot User-Agent
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('ua', [
    'GPTBot/1.0',
    'Mozilla/5.0 (compatible; ClaudeBot/1.0)',
    'PerplexityBot',
    'Bytespider',
    'AhrefsBot/7.0',
    'meta-externalagent/1.1',
    'OAI-SearchBot',
    'Mozilla/5.0 (compatible; bingbot/2.0)',
    'SERankingBacklinksBot/1.0',
    'Mozilla/5.0 AppleWebKit Chrome/98.0.4758.80',
])
def test_known_bot_ua_blocked(ua):
    mw, _ = _make_middleware()
    result = mw._evaluate(_anon_req(ua=ua))
    assert result == {'action': 'block', 'reason': 'known_ua', 'ip': '1.2.3.4'}


def test_bot_ua_check_is_case_insensitive():
    mw, _ = _make_middleware()
    result = mw._evaluate(_anon_req(ua='gptbot/2.0'))
    assert result['reason'] == 'known_ua'


# ---------------------------------------------------------------------------
# Check 2 — IP already blocked in cache
# ---------------------------------------------------------------------------

def test_ip_blocked_in_cache():
    mw, mock_cache = _make_middleware()
    ip = '1.2.3.4'
    mock_cache.get.side_effect = lambda key: 1 if key == RL_IP_BLOCKED.format(ip=ip) else None
    result = mw._evaluate(_anon_req(ip=ip))
    assert result == {'action': 'block', 'reason': 'ip_blocked', 'ip': ip}


# ---------------------------------------------------------------------------
# Check 3a — authenticated user blocked in cache
# ---------------------------------------------------------------------------

def test_auth_user_blocked_in_cache():
    mw, mock_cache = _make_middleware()
    uid = '7'
    mock_cache.get.side_effect = lambda key: (
        1 if key == RL_USER_BLOCKED.format(ns=_NAMESPACE, uid=uid) else None
    )
    result = mw._evaluate(_auth_req(uid=int(uid)))
    assert result == {'action': 'block', 'reason': 'user_blocked', 'ip': '1.2.3.4'}


# ---------------------------------------------------------------------------
# Check 3b — authenticated + suspicious headers
# ---------------------------------------------------------------------------

def test_auth_suspicious_headers_blocked():
    mw, _ = _make_middleware()
    r = _auth_req()
    r.META.pop('HTTP_ACCEPT', None)
    r.META.pop('HTTP_ACCEPT_LANGUAGE', None)
    r.META.pop('HTTP_USER_AGENT', None)
    result = mw._evaluate(r)
    assert result == {'action': 'block', 'reason': 'suspicious_headers_auth', 'ip': '1.2.3.4'}


# ---------------------------------------------------------------------------
# Check 3c — authenticated request rate
# ---------------------------------------------------------------------------

def test_auth_rate_exceeded_blocks_and_marks_user_blocked():
    mw, mock_cache = _make_middleware(auth_rate='5/m')
    mw._incr_with_ttl = MagicMock(return_value=5)  # exactly at threshold
    result = mw._evaluate(_auth_req(uid=7))
    # auth_user_rate has no persistent block key — the window resets naturally
    assert result == {'action': 'block', 'reason': 'auth_user_rate', 'ip': '1.2.3.4'}
    mock_cache.set.assert_not_called()


def test_auth_under_rate_passes():
    mw, mock_cache = _make_middleware(auth_rate='5/m')
    mw._incr_with_ttl = MagicMock(return_value=4)  # one below threshold
    result = mw._evaluate(_auth_req(uid=7))
    assert result == {'action': 'pass', 'ip': '1.2.3.4'}
    mock_cache.set.assert_not_called()


# ---------------------------------------------------------------------------
# Check 4a — anonymous + suspicious headers
# ---------------------------------------------------------------------------

def test_anon_suspicious_headers_blocked():
    mw, _ = _make_middleware()
    r = _anon_req()
    r.META.pop('HTTP_ACCEPT', None)
    r.META.pop('HTTP_ACCEPT_LANGUAGE', None)
    r.META.pop('HTTP_USER_AGENT', None)
    result = mw._evaluate(r)
    assert result == {'action': 'block', 'reason': 'suspicious_headers', 'ip': '1.2.3.4'}


# ---------------------------------------------------------------------------
# Check 4b — anonymous IP request rate
# ---------------------------------------------------------------------------

def test_anon_ip_rate_exceeded_blocks_and_marks_ip_blocked():
    mw, _ = _make_middleware(anon_rate='5/m')
    mw._incr_with_ttl = MagicMock(return_value=5)  # first call (IP counter) hits threshold
    with patch('sapl.middleware.ratelimit._set_block') as mock_set_block:
        result = mw._evaluate(_anon_req())
    assert result == {'action': 'block', 'reason': 'ip_rate', 'ip': '1.2.3.4'}
    mock_set_block.assert_called_once_with(
        RL_IP_BLOCKED.format(ip='1.2.3.4'),
        _index_shard('1.2.3.4', RL_INDEX_BLOCKED_IPS),
        RateLimitMiddleware.BLOCK_TTL,
    )


# ---------------------------------------------------------------------------
# Check 4c — per-namespace/IP/window (UA rotation detection)
# ---------------------------------------------------------------------------

def test_anon_ua_rotation_detected_blocks_and_marks_ip_blocked():
    mw, _ = _make_middleware(anon_rate='5/m')
    # First call (IP counter) is under threshold; second (window counter) hits it.
    mw._incr_with_ttl = MagicMock(side_effect=[4, 5])
    with patch('sapl.middleware.ratelimit._set_block') as mock_set_block:
        result = mw._evaluate(_anon_req())
    assert result == {'action': 'block', 'reason': 'ua_rotation', 'ip': '1.2.3.4'}
    mock_set_block.assert_called_once_with(
        RL_IP_BLOCKED.format(ip='1.2.3.4'),
        _index_shard('1.2.3.4', RL_INDEX_BLOCKED_IPS),
        RateLimitMiddleware.BLOCK_TTL,
    )


def test_anon_under_all_thresholds_passes():
    mw, mock_cache = _make_middleware(anon_rate='5/m')
    mw._incr_with_ttl = MagicMock(return_value=4)  # both counters below threshold
    result = mw._evaluate(_anon_req())
    assert result == {'action': 'pass', 'ip': '1.2.3.4'}
    mock_cache.set.assert_not_called()


# ---------------------------------------------------------------------------
# __call__ — block returns 429, pass forwards to get_response
# ---------------------------------------------------------------------------

def test_call_block_returns_429_with_retry_after_header():
    mw, _ = _make_middleware()
    mw._evaluate = MagicMock(return_value={'action': 'block', 'reason': 'known_ua', 'ip': '1.2.3.4'})
    response = mw(_factory.get('/'))
    assert response.status_code == 429
    assert response['Retry-After'] == str(RateLimitMiddleware.BLOCK_TTL)
    mw.get_response.assert_not_called()


def test_call_ip_prefix_block_returns_403_without_retry_after_header():
    mw, _ = _make_middleware()
    mw._evaluate = MagicMock(return_value={'action': 'block', 'reason': 'ip_prefix_blocked', 'ip': '1.2.3.4'})
    response = mw(_factory.get('/'))
    assert response.status_code == 403
    assert 'Retry-After' not in response
    assert response['X-RateLimit-Reason'] == 'ip_prefix_blocked'
    mw.get_response.assert_not_called()


def test_call_pass_forwards_request_to_get_response():
    mw, _ = _make_middleware()
    mw._evaluate = MagicMock(return_value={'action': 'pass', 'ip': '1.2.3.4'})
    request = _anon_req()
    mw(request)
    mw.get_response.assert_called_once_with(request)


def test_call_rejects_duplicate_page_param_with_400():
    mw, _ = _make_middleware()
    request = _factory.get('/sessao/pesquisar-sessao', data={'page': ['3', '2', '3']})
    response = mw(request)
    assert response.status_code == 400
    assert response['X-RateLimit-Reason'] == 'param_pollution'
    mw.get_response.assert_not_called()


def test_call_allows_single_page_param():
    mw, _ = _make_middleware()
    mw._evaluate = MagicMock(return_value={'action': 'pass', 'ip': '1.2.3.4'})
    request = _factory.get('/sessao/pesquisar-sessao', data={'page': '2'})
    mw(request)
    mw.get_response.assert_called_once_with(request)


def test_call_allows_no_page_param():
    mw, _ = _make_middleware()
    mw._evaluate = MagicMock(return_value={'action': 'pass', 'ip': '1.2.3.4'})
    request = _factory.get('/sessao/pesquisar-sessao')
    mw(request)
    mw.get_response.assert_called_once_with(request)


# ---------------------------------------------------------------------------
# _is_same_origin
# ---------------------------------------------------------------------------

def test_is_same_origin_no_headers_returns_false():
    r = _factory.get('/api/materia/')
    r.META['SERVER_NAME'] = 'sapl.example.com'
    r.META['SERVER_PORT'] = '80'
    r.META.pop('HTTP_ORIGIN', None)
    r.META.pop('HTTP_REFERER', None)
    assert _is_same_origin(r) is False


def test_is_same_origin_matching_origin():
    r = _factory.get('/api/materia/', SERVER_NAME='sapl.example.com', SERVER_PORT='80')
    r.META['HTTP_ORIGIN'] = 'https://sapl.example.com'
    assert _is_same_origin(r) is True


def test_is_same_origin_mismatched_origin():
    r = _factory.get('/api/materia/', SERVER_NAME='sapl.example.com', SERVER_PORT='80')
    r.META['HTTP_ORIGIN'] = 'https://other.example.com'
    assert _is_same_origin(r) is False


def test_is_same_origin_wrong_origin_blocks_even_if_referer_matches():
    """If Origin is present and wrong, Referer must not be consulted."""
    r = _factory.get('/api/materia/', SERVER_NAME='sapl.example.com', SERVER_PORT='80')
    r.META['HTTP_ORIGIN'] = 'https://evil.com'
    r.META['HTTP_REFERER'] = 'https://sapl.example.com/page/'
    assert _is_same_origin(r) is False


def test_is_same_origin_referer_used_when_no_origin():
    r = _factory.get('/api/materia/', SERVER_NAME='sapl.example.com', SERVER_PORT='80')
    r.META.pop('HTTP_ORIGIN', None)
    r.META['HTTP_REFERER'] = 'https://sapl.example.com/page/?q=1'
    assert _is_same_origin(r) is True


def test_is_same_origin_port_stripped_from_both_sides():
    """Host with port and Origin without port must match after normalization."""
    r = _factory.get('/api/materia/', SERVER_NAME='sapl.example.com', SERVER_PORT='8000')
    r.META['HTTP_HOST'] = 'sapl.example.com:8000'
    r.META['HTTP_ORIGIN'] = 'http://sapl.example.com'
    assert _is_same_origin(r) is True


def test_is_same_origin_case_insensitive():
    r = _factory.get('/api/materia/', SERVER_NAME='sapl.example.com', SERVER_PORT='80')
    r.META['HTTP_ORIGIN'] = 'https://SAPL.EXAMPLE.COM'
    assert _is_same_origin(r) is True


# ---------------------------------------------------------------------------
# _handle_api — OPTIONS and same-origin bypass
# ---------------------------------------------------------------------------

def _api_req(ip='1.2.3.4', ua='Mozilla/5.0', path='/api/materia/', method='GET', extra_meta=None):
    """Anonymous /api/ request with browser headers."""
    request = _factory.generic(method, path)
    request.META.update({'REMOTE_ADDR': ip, 'HTTP_USER_AGENT': ua, **_NORMAL_HEADERS})
    if extra_meta:
        request.META.update(extra_meta)
    request.user = MagicMock(is_authenticated=False)
    return request


def test_api_options_passes_without_counting():
    mw, _ = _make_middleware()
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock()
    request = _api_req(method='OPTIONS')
    mw(request)
    mw.get_response.assert_called_once_with(request)
    mw._incr_with_ttl.assert_not_called()


def test_api_same_origin_passes_without_counting():
    mw, _ = _make_middleware()
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock()
    request = _api_req(extra_meta={
        'SERVER_NAME': 'sapl.example.com',
        'SERVER_PORT': '80',
        'HTTP_HOST': 'sapl.example.com',
        'HTTP_ORIGIN': 'https://sapl.example.com',
    })
    mw(request)
    mw.get_response.assert_called_once_with(request)
    mw._incr_with_ttl.assert_not_called()


def test_api_malicious_origin_is_not_same_origin():
    mw, _ = _make_middleware(api_threshold=999)
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock(return_value=1)
    request = _api_req(extra_meta={
        'SERVER_NAME': 'sapl.example.com',
        'SERVER_PORT': '80',
        'HTTP_HOST': 'sapl.example.com',
        'HTTP_ORIGIN': 'https://evil.com?x=sapl.example.com',
    })
    mw(request)
    # Must reach the counter (not short-circuit as same-origin)
    mw._incr_with_ttl.assert_called_once()


# Same-origin headers a spoofing client can trivially forge — Origin/Referer
# carry no authentication, so they must never override an active block.
_SAME_ORIGIN_META = {
    'SERVER_NAME': 'sapl.example.com',
    'SERVER_PORT': '80',
    'HTTP_HOST': 'sapl.example.com',
    'HTTP_ORIGIN': 'https://sapl.example.com',
}


def test_api_same_origin_does_not_bypass_global_ip_block():
    mw, mock_cache = _make_middleware()
    ip = '1.2.3.4'
    mock_cache.get.side_effect = lambda key: 1 if key == RL_IP_BLOCKED.format(ip=ip) else None
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock()
    request = _api_req(ip=ip, extra_meta=_SAME_ORIGIN_META)

    response = mw(request)

    mw.get_response.assert_not_called()
    assert response.status_code == 429
    assert response['X-RateLimit-Reason'] == 'global_ip_blocked'


def test_api_same_origin_does_not_bypass_api_ip_block():
    mw, mock_cache = _make_middleware()
    ip = '1.2.3.4'
    blocked_key = RL_API_IP_BLOCKED.format(ns=_NAMESPACE, ip=ip)
    mock_cache.get.side_effect = lambda key: 1 if key == blocked_key else None
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock()
    request = _api_req(ip=ip, extra_meta=_SAME_ORIGIN_META)

    response = mw(request)

    mw.get_response.assert_not_called()
    assert response.status_code == 429
    assert response['X-RateLimit-Reason'] == 'api_ip_blocked'


def test_api_same_origin_does_not_bypass_ip_prefix_block(_seed_prefix_blocklist):
    mw, _ = _make_middleware()
    _seed_prefix_blocklist(['1.2.3'])
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock()
    request = _api_req(ip='1.2.3.4', extra_meta=_SAME_ORIGIN_META)

    response = mw(request)

    mw.get_response.assert_not_called()
    assert response.status_code == 403
    assert response['X-RateLimit-Reason'] == 'ip_prefix_blocked'


def test_api_same_origin_still_skips_quota_and_rate_limit_when_not_blocked():
    """Legitimate same-origin polling keeps its original exemption from accounting."""
    mw, _ = _make_middleware()
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock()
    request = _api_req(extra_meta=_SAME_ORIGIN_META)

    response = mw(request)

    mw.get_response.assert_called_once_with(request)
    mw._check_api_quota.assert_not_called()
    mw._incr_with_ttl.assert_not_called()
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# _handle_api — Check 3a: IP-prefix block (operator-curated deny list)
# ---------------------------------------------------------------------------

def test_api_blocks_on_ip_prefix_before_quota_checks(_seed_prefix_blocklist):
    mw, mock_cache = _make_middleware()
    _seed_prefix_blocklist(['1.2.3'])
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock()
    request = _api_req(ip='1.2.3.4')

    response = mw(request)

    mw.get_response.assert_not_called()
    mw._check_api_quota.assert_not_called()
    mw._incr_with_ttl.assert_not_called()
    assert response.status_code == 403
    assert response['X-RateLimit-Reason'] == 'ip_prefix_blocked'


def test_api_passes_through_when_ip_not_in_prefix_list(_seed_prefix_blocklist):
    mw, _ = _make_middleware(api_threshold=999)
    _seed_prefix_blocklist(['9.9.9'])
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock(return_value=1)
    request = _api_req(ip='1.2.3.4')

    mw(request)

    mw.get_response.assert_called_once_with(request)


# ---------------------------------------------------------------------------
# _handle_api — rate limiting and block key isolation
# ---------------------------------------------------------------------------

def test_api_external_request_increments_api_counter():
    mw, _ = _make_middleware(api_threshold=10)
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock(return_value=5)  # under threshold
    request = _api_req()
    response = mw(request)
    mw.get_response.assert_called_once_with(request)
    call_args = mw._incr_with_ttl.call_args[0]
    assert call_args[0] == RL_API_IP_REQUESTS.format(ns=_NAMESPACE, ip='1.2.3.4')


def test_api_threshold_exceeded_creates_api_block_not_global_block():
    mw, _ = _make_middleware(api_threshold=5)
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock(return_value=5)  # at threshold
    request = _api_req()
    with patch('sapl.middleware.ratelimit._set_block') as mock_set_block:
        response = mw(request)
    assert response.status_code == 429
    mock_set_block.assert_called_once()
    block_key = mock_set_block.call_args[0][0]
    assert block_key == RL_API_IP_BLOCKED.format(ns=_NAMESPACE, ip='1.2.3.4')
    assert block_key != RL_IP_BLOCKED.format(ip='1.2.3.4')


def test_api_global_block_also_blocks_api():
    mw, mock_cache = _make_middleware()
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock()
    ip = '1.2.3.4'
    mock_cache.get.side_effect = lambda key: 1 if key == RL_IP_BLOCKED.format(ip=ip) else None
    response = mw(_api_req(ip=ip))
    assert response.status_code == 429
    assert response['X-RateLimit-Reason'] == 'global_ip_blocked'
    mw._incr_with_ttl.assert_not_called()


def test_api_specific_block_blocks_api_only():
    mw, mock_cache = _make_middleware()
    mw._check_api_quota = MagicMock(return_value=None)
    mw._incr_with_ttl = MagicMock()
    ip = '1.2.3.4'
    mock_cache.get.side_effect = lambda key: 1 if key == RL_API_IP_BLOCKED.format(ns=_NAMESPACE, ip=ip) else None
    response = mw(_api_req(ip=ip))
    assert response.status_code == 429
    assert response['X-RateLimit-Reason'] == 'api_ip_blocked'
    mw._incr_with_ttl.assert_not_called()


def test_api_block_response_is_json_with_retry_after():
    mw, _ = _make_middleware(api_block_seconds=120)
    resp = mw._api_block_response('api_threshold_exceeded')
    assert resp.status_code == 429
    assert 'application/json' in resp['Content-Type']
    assert resp['Retry-After'] == '120'
    assert resp['X-RateLimit-Reason'] == 'api_threshold_exceeded'


def test_api_auth_user_daily_quota_exceeded_returns_429():
    """Auth users are subject to the same daily quota as anon callers (keyed by IP)."""
    mw, _ = _make_middleware()
    request = _api_req(ip='10.0.0.1')
    request.user = MagicMock(is_authenticated=True, pk=42)
    mw.api_quota_daily = 1

    with patch('sapl.middleware.ratelimit._hincrby_with_ttl', return_value=2):
        resp = mw(request)

    assert resp.status_code == 429
    assert resp['X-RateLimit-Reason'] == 'quota_daily'


def test_api_weekly_quota_exceeded_returns_429():
    """Weekly quota block fires when daily passes but weekly counter exceeds limit."""
    mw, _ = _make_middleware()
    request = _api_req(ip='10.0.0.2')
    mw.api_quota_daily = 999999
    mw.api_quota_weekly = 1

    # daily returns 1 (under limit), weekly returns 2 (over limit)
    with patch('sapl.middleware.ratelimit._hincrby_with_ttl', side_effect=[1, 2]):
        resp = mw(request)

    assert resp.status_code == 429
    assert resp['X-RateLimit-Reason'] == 'quota_weekly'


def test_api_quota_uses_hash_keys():
    """_check_api_quota calls _hincrby_with_ttl with HASH keys (no IP in key name)."""
    from datetime import date
    mw, _ = _make_middleware()
    request = _api_req(ip='10.0.0.3')
    mw.api_quota_daily = 999999
    mw.api_quota_weekly = 999999

    with patch('sapl.middleware.ratelimit._hincrby_with_ttl', return_value=1) as mock_h:
        mw._check_api_quota(request)

    today = date.today()
    iso = today.isocalendar()
    expected_daily_hash = API_QUOTA_DAILY_HASH.format(ns=_NAMESPACE, date=today.isoformat())
    expected_weekly_hash = API_QUOTA_WEEKLY_HASH.format(
        ns=_NAMESPACE, week=f'{iso[0]}-W{iso[1]:02d}'
    )
    calls = mock_h.call_args_list
    assert calls[0][0][0] == expected_daily_hash   # first arg of first call = hash key
    assert calls[1][0][0] == expected_weekly_hash  # first arg of second call = hash key
    # IP is the field (second positional arg), not embedded in the key
    assert '10.0.0.3' not in calls[0][0][0]
    assert '10.0.0.3' not in calls[1][0][0]


def test_inc_block_metric_uses_hash_key():
    """_inc_block_metric calls _hincrby_with_ttl with a HASH key; reason is the field."""
    from datetime import date
    mw, _ = _make_middleware()
    today_str = date.today().isoformat()
    expected_key = f'rl:metrics:{_NAMESPACE}:{today_str}'

    with patch('sapl.middleware.ratelimit._hincrby_with_ttl') as mock_h:
        mw._inc_block_metric('ip_rate')

    mock_h.assert_called_once()
    args = mock_h.call_args[0]
    assert args[0] == expected_key, f'hash key mismatch: {args[0]!r}'
    assert args[1] == 'ip_rate',    f'field (reason) mismatch: {args[1]!r}'
    assert 'ip_rate' not in args[0], 'reason must be HASH field, not embedded in key'


def test_non_api_path_uses_global_evaluate_not_api_handler():
    mw, _ = _make_middleware()
    mw._handle_api = MagicMock()
    mw._evaluate = MagicMock(return_value={'action': 'pass', 'ip': '1.2.3.4'})
    mw(_anon_req(path='/'))
    mw._handle_api.assert_not_called()
    mw._evaluate.assert_called_once()
