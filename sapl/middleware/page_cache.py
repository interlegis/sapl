"""
AnonCachePageMixin — anonymous-only Django view response caching.

Why anonymous-only?
  - Authenticated responses include CSRF tokens and user-specific UI fragments
    (edit/delete action buttons injected by SAPL's CRUD framework).  Caching
    those would serve stale or wrong data to other users.
  - Bot traffic is entirely anonymous.  A 2-minute cache converts hundreds of
    identical list-view DB queries into a single one — exactly the workload
    that triggers OOM in the fleet.

How it works:
  - `dispatch()` short-circuits to the normal (uncached) path for any
    authenticated request.
  - For anonymous GET/HEAD requests, the response is stored in the 'default'
    Redis cache under a key that includes the full URL (scheme + host + path +
    query string).  The Django cache framework handles key construction and
    TTL expiry automatically.
  - HTTPS and HTTP requests are stored under separate keys (Django default).

Usage:

    from sapl.middleware.page_cache import AnonCachePageMixin

    class MyListView(AnonCachePageMixin, ListView):
        anon_cache_ttl = settings.PAGE_CACHE_TTL_LIST   # 120 s

    class MyDetailView(AnonCachePageMixin, DetailView):
        anon_cache_ttl = settings.PAGE_CACHE_TTL_DETAIL  # 300 s

TTL reference (see settings.PAGE_CACHE_TTL_*):

    View type                                 Default TTL
    ─────────────────────────────────────────────────────
    Public list   (norma, materia, sessao…)   120 s  (PAGE_CACHE_TTL_LIST)
    Public detail (norma, materia, sessao…)   300 s  (PAGE_CACHE_TTL_DETAIL)
    Stable detail (parlamentar, comissão)     600 s  (PAGE_CACHE_TTL_STABLE)

Invalidation:
  The cache TTL is intentionally short (≤ 10 min) so stale content expires
  on its own.  Explicit invalidation is not implemented — legislative data
  changes infrequently and short TTLs are acceptable.
"""

from django.conf import settings
from django.views.decorators.cache import cache_page, never_cache
from django.utils.decorators import method_decorator


class AnonCachePageMixin:
    """
    Cache the full view response for anonymous (unauthenticated) requests.

    Set `anon_cache_ttl` on the subclass to override the default TTL.
    Authenticated requests always bypass the cache.
    """

    # Override per view class.  Use settings.PAGE_CACHE_TTL_* for consistency.
    anon_cache_ttl = getattr(settings, 'PAGE_CACHE_TTL_LIST', 120)

    def dispatch(self, request, *args, **kwargs):
        if getattr(request, 'user', None) and request.user.is_authenticated:
            # Authenticated: skip cache entirely — response may contain
            # user-specific controls (CSRF token, edit/delete buttons).
            handler = never_cache(
                lambda req, *a, **kw: super(AnonCachePageMixin, self).dispatch(req, *a, **kw)
            )
            return handler(request, *args, **kwargs)

        # Anonymous: wrap the parent dispatch in cache_page so Django stores
        # the rendered response in the 'default' cache for anon_cache_ttl seconds.
        handler = cache_page(self.anon_cache_ttl)(
            lambda req, *a, **kw: super(AnonCachePageMixin, self).dispatch(req, *a, **kw)
        )
        return handler(request, *args, **kwargs)
