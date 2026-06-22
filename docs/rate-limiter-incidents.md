# Rate Limiter Incidents

This document records real rate-limiting incidents, the root-cause analysis performed for each, the fixes applied, and the architectural discussion that followed. New incidents should be appended under their own section.

---

## PatoBranco-PR — 2026-05-06

### Symptom

Councilmembers reported being unable to access the voting interface during a live plenary session. The error was HTTP 429. Two blocking events occurred:

| Event | Start | Recovery | Duration |
|-------|-------|----------|----------|
| 1 | 13:51:23 | ~14:01 | ~10 min |
| 2 | 14:22:30 | ~14:25 | ~3 min |

Both recovered **before** the Django `BLOCK_TTL` of 300 seconds, which was the first diagnostic clue.

### Environment

- NAT IP: `200.175.17.66` (reported range `200.175.17.66/29`)
- Secondary range: `187.109.99.234/30`
- Peak observed: **24 requests/second** from that IP (confirmed in OpenSearch, 14:22:31)
- Paths involved: `/voto-individual/`, `/sessao/pauta-sessao/2600/`, `/sessao/2600/ordemdia`

### Root Cause

Multiple councilmembers share a single public IP via NAT. When a vote opened, all of them reloaded their browser simultaneously. Nginx saw the combined traffic as a single client exhausting its burst bucket and returned 429 — before any request reached Django.

```
                     ┌─────────────────────────────────────────┐
                     │              nginx                       │
                     │                                         │
  Councilmember A ──►│  IP: 200.175.17.66                      │
  Councilmember B ──►│  IP: 200.175.17.66  ──► burst bucket    │──► 429 (bucket full)
  Councilmember C ──►│  IP: 200.175.17.66      exhausted       │
        ...          │                                         │
                     └─────────────────────────────────────────┘
                                        │
                                        │ (never reached)
                                        ▼
                     ┌─────────────────────────────────────────┐
                     │           Django middleware              │
                     │                                         │
                     │  rl:ip:<ip>:reqs     (never incremented)│
                     │  rl:user:<id>:reqs   (never incremented)│
                     │  Redis block key     (never written)    │
                     └─────────────────────────────────────────┘
```

### Why Recovery Was Faster Than 300 Seconds

Django's block mechanism (`_set_block()`) was **never triggered**. The NAT IP was never written to Redis. The 429s came entirely from nginx's token bucket being exhausted.

Recovery happened when the synchronized burst subsided (vote ended, users stopped reloading). The nginx bucket refilled at its configured rate. No TTL expiry was involved — recovery time was variable because it depended on how depleted the bucket was at the end of each burst, not on a fixed timer.

Had Django's block fired, the outage would have been exactly 300 seconds both times. The variable durations (10 min vs 3 min) confirm nginx was the sole actor.

### The Polling Source

`voto_individual.html` contains a `setTimeout(location.reload, 30000)` — the page reloads itself every 30 seconds. When councilmembers opened the voting page at roughly the same time (vote announcement), their reload timers aligned. Each 30-second tick fired a synchronized burst from all clients behind the NAT.

`/sessao/<pk>/ordemdia` and `/sessao/pauta-sessao/<pk>/` are not polled by JavaScript — they are normal page navigations. They appeared in the burst because councilmembers navigated to them at the same moment as the vote opened.

### Two-Layer Rate Limiting Architecture

```
                        ┌──────────────────────────────────────────────────────┐
  Incoming request       │  nginx                                                │
  ─────────────────────►│                                                       │
                        │  limit_req zone=sapl_general  ← IP-only, no auth     │
                        │  burst=${NGINX_BURST_GENERAL} nodelay                 │
                        │                                                       │
                        │  If bucket full → 429 immediately                    │
                        │  Redis: nothing written                               │
                        └───────────────────────┬──────────────────────────────┘
                                                │ (only if bucket has room)
                                                ▼
                        ┌──────────────────────────────────────────────────────┐
                        │  Django RateLimitMiddleware                           │
                        │                                                       │
                        │  1. Bypass check  ← RATE_LIMIT_BYPASS_PATHS          │
                        │  2. API quota check (if /api/)                       │
                        │  3. _evaluate()                                       │
                        │     a. IP block check  (Redis rl:ip:<ip>:blocked)    │
                        │     b. User block check (Redis rl:user:<id>:blocked) │
                        │     c. Rate counter    (rl:ip:<ip>:reqs)             │
                        │     d. User counter    (rl:user:<id>:reqs)           │
                        │                                                       │
                        │  If rate exceeded → SET block key (TTL=300s)         │
                        │                  → ZADD rl:index:blocked_ips         │
                        └──────────────────────────────────────────────────────┘
```

**The core mismatch:** Django tracks per-user buckets (`rl:user:<id>:reqs`) which are NAT-safe. Nginx tracks per-IP buckets which collapse all users behind a NAT into one. Nginx fires first, so Django's smarter per-user accounting is never consulted during a burst.

### Fix Applied

Added nginx `location` blocks for session and voting paths that pass requests through **without** `limit_req`. These regex locations take priority over the catch-all `location /` by nginx matching rules.

**`docker/config/nginx/sapl.conf`:**
```nginx
location ~ ^/voto-individual/ {
    proxy_set_header X-Request-ID      $req_id;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host              $http_host;
    proxy_redirect off;
    proxy_pass http://sapl_server;
}

location ~ ^/sessao/\d+ {
    proxy_set_header X-Request-ID      $req_id;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host              $http_host;
    proxy_redirect off;
    proxy_pass http://sapl_server;
}
```

**`sapl/settings.py`** — `RATE_LIMIT_BYPASS_PATHS` extended to match:
```python
RATE_LIMIT_BYPASS_PATHS = [
    r'^/painel/\d+/dados$',
    r'^/voto-individual/',
    r'^/sessao/\d+',
    r'^/sessao/pauta-sessao/\d+/',
]
```

These paths are safe to exempt because:
- They require an authenticated session cookie to perform any meaningful action.
- Django's per-user rate counter still runs as a backstop.
- The cost of a false-positive block (councilmember unable to vote) outweighs the risk of abuse on these URLs.

---

## Architectural Discussion

### Why Increasing Burst Rates Is Not the Right Fix

`burst` controls how many requests above the sustained rate are allowed in a spike before 429 fires. A larger burst absorbs thundering herds from NAT but also allows more requests from burst-style attackers (scanners, credential stuffers) before the throttle engages. It is the same knob, pulled in opposite directions.

The correct dimensioning formula for a legislative house would be:

```
burst ≥ users_behind_NAT × tabs_per_user × requests_per_page_load
```

For a large state assembly (90 deputies, 2 tabs each) this exceeds 180 — a burst value that renders rate limiting ineffective against automated tools.

**Conclusion:** burst tuning is not the right tool for this problem. Exemption of known-safe high-frequency paths is.

### The Multi-Tab Problem

Staff members commonly open multiple SAPL tabs simultaneously. Each tab has its own reload timer. If 10 staff members have 3 tabs open, a synchronized event generates 30+ requests from the NAT IP even before councilmembers are counted. This means the bucket can be pre-exhausted before the voting burst even starts.

This further reinforces that IP-based rate limiting is the wrong unit for authenticated traffic in a shared-office environment.

### Why Per-User Rate Limiting Does Not Fully Solve This

Django already increments both `rl:ip:<ip>:reqs` and `rl:user:<id>:reqs`. The per-user counter is NAT-safe. But it never runs during a burst because nginx drops the request first.

Moving rate limiting for authenticated users to the Django layer only (removing nginx `limit_req` for authenticated paths) would make per-user counting the effective control. The obstacle is that nginx cannot distinguish authenticated from anonymous requests without reading and resolving the session cookie — which requires a database or Redis lookup nginx cannot perform natively.

### Architectural Solutions

| Approach | Effort | Solves NAT problem | Protects against bots |
|----------|--------|-------------------|----------------------|
| Nginx bypass for known session paths *(done)* | Low | Yes, for bypassed paths | Yes, general paths still rate-limited |
| Increase `NGINX_BURST_GENERAL` | Trivial | Partially | Weakens bot protection |
| Nginx `limit_req_zone` keyed on session cookie string | Medium | Yes (per-session token, not per-IP) | Yes, each session has own bucket |
| Move all auth-path rate limiting to Django only | Medium | Yes | Depends on Django rate correctly tuned |
| Replace `setTimeout(location.reload)` with WebSocket/SSE push | High | Yes — eliminates synchronized reloads entirely | N/A |

### WebSocket / SSE Consideration

The 30-second self-reload in `voto_individual.html` is the synchronization mechanism that creates the thundering herd. If the server pushed state changes (vote opened, result published) instead of the client polling by reloading, the synchronized burst would not exist regardless of how many users or tabs are open.

A full WebSocket rewrite (Django Channels + Redis pub/sub channel layer) would:
- Eliminate polling bursts on session/voting paths
- Make vote-state updates instantaneous instead of up to 30 seconds late
- Require nginx configuration for `Upgrade: websocket` proxying

The nginx bypass is the correct operational fix for now. The WebSocket rewrite is the correct architectural fix for the future. They are not substitutes — the bypass would remain useful for the initial WebSocket handshake, which is still an HTTP request subject to burst limits.

---

## Diagrams — Issues, Solutions, and Trade-offs (2026-05-06/07)

---

### 1. NAT Thundering Herd — Before the Fix

During a live vote all councilmembers reload simultaneously. nginx sees one
IP, exhausts its bucket, and returns 429 before Django is ever involved.
Django's per-user counter (NAT-safe) is never consulted.

```
  Office / Chamber — behind one NAT IP (200.175.17.66)
  ┌──────────────────────────────────────────────────────┐
  │  Councilmember A  browser reload ──┐                 │
  │  Councilmember B  browser reload ──┤                 │
  │  Councilmember C  browser reload ──┤  ~24 req/s      │
  │  Staff tab 1      browser reload ──┤  same public IP │
  │  Staff tab 2      browser reload ──┘                 │
  └────────────────────────────┬─────────────────────────┘
                               │ all requests look identical to nginx
                               ▼
             ┌─────────────────────────────────────┐
             │  nginx  sapl_general                │
             │  rate=30r/m   burst=60  nodelay     │
             │                                     │
             │  token bucket: 0 tokens remaining   │
             │  → 429 returned immediately         │
             └──────────────────┬──────────────────┘
                                │
                    ╳ Django never reached
                    ╳ rl:ip:{ip}:reqs  never incremented
                    ╳ rl:user:{uid}:reqs  never incremented
                    ╳ per-user NAT-safe counter  never consulted
                                │
                                ▼
                  429 for all N users in the org
                  recovery: wait for nginx bucket refill
                  (~3–10 min depending on depletion)
                  NOT a Django 300s block (Redis never written)
```

---

### 2. NAT Thundering Herd — After the Session Bypass Fix

Session and voting paths have dedicated nginx `location` blocks with no
`limit_req`. Regex locations take priority over `location /`.

```
  Office / Chamber — behind one NAT IP
  ┌──────────────────────────────────────────────────────┐
  │  Councilmember A  /voto-individual/   reload ──┐     │
  │  Councilmember B  /voto-individual/   reload ──┤     │
  │  Councilmember C  /sessao/2600/ordemdia ───────┤     │
  │  Staff tab        /sessao/pauta-sessao/2600/ ──┘     │
  └────────────────────────────┬─────────────────────────┘
                               │
                               ▼
             ┌─────────────────────────────────────┐
             │  nginx                              │
             │                                     │
             │  location ~ ^/voto-individual/  ─┐  │
             │  location ~ ^/sessao/\d+        ─┤  │  no limit_req
             │  location ~ ^/painel/\d+/dados  ─┘  │  pass through
             └──────────────────┬──────────────────┘
                                │
                                ▼
             ┌─────────────────────────────────────┐
             │  Django RateLimitMiddleware          │
             │                                     │
             │  RATE_LIMIT_BYPASS_PATHS match?      │
             │  → yes: return get_response()        │
             │    (no counter, no block check)      │
             └──────────────────┬──────────────────┘
                                │
                                ▼
                          ✓ View served
                  All N users get their page
```

---

### 3. nginx Zone Architecture — Before vs After

**Before (single shared zone)**

```
  All traffic (HTML + media + API)
          │
          ▼
  ┌───────────────────────────────┐
  │  sapl_general                 │   ← one bucket per IP
  │  rate=30r/m   burst=60        │
  │                               │
  │  /media/page.pdf  ──────────┐ │   ← media request drains
  │  /materia/123/    ──────────┤ │     the same bucket as
  │  /api/materia/?   ──────────┘ │     the HTML page
  └───────────────────────────────┘
  
  Problem: a page with 20 media attachments
  burns 20 tokens from the page-load budget
```

**After (four independent zones)**

```
  ┌─────────────────┐  location /
  │  sapl_general   │  rate=90r/m   burst=180  — HTML page requests
  └─────────────────┘

  ┌─────────────────┐  location /media/
  │  sapl_media     │  rate=180r/m  burst=180  — media downloads
  └─────────────────┘                            own bucket, never
                                                 drains page quota
  ┌─────────────────┐  location /api/
  │  sapl_api       │  rate=60r/m   burst=120  — API calls
  └─────────────────┘                            quota layer is
                                                 real constraint
  ┌─────────────────┐  location /relatorios/
  │  sapl_heavy     │  rate=10r/m   burst=20   — PDF generation
  └─────────────────┘  nodelay                   tight by design

  Session/voting paths: NO zone — exempt from limit_req entirely
  Static files /static/: NO zone — served directly from disk
```

---

### 4. Anonymous /api/ NAT Problem — Before vs After

**Before**

```
  Office — 10 staff, JS polling /api/ every 5s = 120 req/min combined
                               │
                               ▼
             ┌─────────────────────────────────────┐
             │  nginx sapl_general (was shared)    │
             │  burst not yet exhausted → pass     │
             └──────────────────┬──────────────────┘
                                │
                                ▼
             ┌─────────────────────────────────────┐
             │  Django _evaluate_anonymous          │
             │                                     │
             │  INCR rl:ip:{ip}:reqs               │
             │  count = 120 ≥ threshold (120/m)    │
             │                                     │
             │  SET rl:ip:{ip}:blocked  EX 300     │◄── block key written
             │  ZADD rl:index:blocked_ips           │    affects ALL paths
             └──────────────────┬──────────────────┘
                                │
                                ▼
          Next request to /materia/, /sessao/, /voto-individual/ ...
                   → 429 ip_blocked  (300s)
          Entire org locked out of ALL SAPL pages
          because of JS polling the API
```

**After**

```
  Office — 10 staff, JS polling /api/ every 5s = 120 req/min combined
                               │
                               ▼
             ┌─────────────────────────────────────┐
             │  nginx sapl_api                     │
             │  rate=60r/m   burst=120  nodelay    │
             │  throttles burst, passes remainder  │
             └──────────────────┬──────────────────┘
                                │
                                ▼
             ┌─────────────────────────────────────┐
             │  Django: quota check                │
             │  500 req/day not exceeded → pass    │
             └──────────────────┬──────────────────┘
                                │
                                ▼
             ┌─────────────────────────────────────┐
             │  Anonymous /api/ early return       │
             │                                     │
             │  rl:ip:{ip}:reqs  NOT incremented   │◄── no counter
             │  rl:ip:{ip}:blocked  NOT written    │◄── no block key
             └──────────────────┬──────────────────┘
                                │
                                ▼
                          ✓ View served
              Page requests from same IP unaffected
```

---

### 5. Authenticated Rate Breach — Before vs After

**Before**

```
  Authenticated user clicks rapidly: 241 requests in 60s
                               │
                               ▼
             ┌─────────────────────────────────────┐
             │  _evaluate_authenticated             │
             │  INCR rl:user:{uid}:reqs  → 241     │
             │  count ≥ 240 (auth threshold)       │
             │                                     │
             │  SET rl:user:{uid}:blocked  EX 300  │◄── 5-minute lockout
             │  ZADD rl:index:blocked_users         │
             └──────────────────┬──────────────────┘
                                │
                                ▼
                  All requests for 300s → 429 user_blocked
                  User must wait 5 minutes to do anything
                  No way to self-recover sooner
```

**After**

```
  Authenticated user clicks rapidly: 241 requests in 60s
                               │
                               ▼
             ┌─────────────────────────────────────┐
             │  _evaluate_authenticated             │
             │  INCR rl:user:{uid}:reqs  → 241     │
             │  count ≥ 240 (auth threshold)       │
             │                                     │
             │  return 429 auth_user_rate           │◄── this request only
             │  (no SET, no ZADD)                  │◄── no block key written
             └──────────────────┬──────────────────┘
                                │
                  Counter TTL = 60s (auth_window)
                                │
                                ▼
                  T+60s: rl:user:{uid}:reqs expires
                  User automatically recovers
                  No admin intervention needed
```

---

### 6. Enforcement Stack Per Path — Trade-off Summary

```
Path                    nginx zone       Django counter    Block written?  Notes
──────────────────────  ───────────────  ────────────────  ──────────────  ──────────────────────────────
/static/*               none             none              —               disk-served, zero Django cost
/painel/<pk>/dados      none             none              —               bypass: high-freq polling
/voto-individual/*      none             none              —               bypass: live vote
/sessao/<pk>/*          none             none              —               bypass: live session
/sessao/pauta-sessao/*  none             none              —               bypass: live session
/media/*                sapl_media       anon IP / auth    anon: yes       auth gate in serve_media()
                        180r/m b=180     counter runs      auth: no
/api/* (anonymous)      sapl_api         quota only        no              ← key change: no IP counter,
                        60r/m  b=120     500/day           —               no collateral NAT block
/api/* (authenticated)  sapl_api         per-user 240/m    no (soft)       per-user, NAT-safe
                        60r/m  b=120     counter runs
/relatorios/*           sapl_heavy       anon/auth runs    anon: yes       tight rate — PDF generation
                        10r/m  b=20      at Django         auth: no
/* (everything else)    sapl_general     anon/auth runs    anon: yes       normal page navigation
                        90r/m  b=180     at Django         auth: no        auth gets 240/m soft limit
```

**Legend:**
- `anon: yes` — anonymous IP gets a 300s block key on breach
- `auth: no` — authenticated users get 429 for that request, window resets in 60s, no persistent block
- `none` — no rate limiting at either layer (path is exempt)

---

### 7. The Fundamental NAT Constraint

```
  IP-based rate limiting cannot distinguish these two scenarios:

  Scenario A — Legitimate (15 users, 1 tab each, vote opens)
  ┌──────────────────────────────────────────────────────┐
  │  User 1 ──► GET /voto-individual/                    │
  │  User 2 ──► GET /voto-individual/      15 req/s      │
  │  ...                                  1 public IP   │
  │  User 15 ──► GET /sessao/2600/ordemdia               │
  └──────────────────────────────────────────────────────┘

  Scenario B — Bot (1 process, 15 threads, scraping)
  ┌──────────────────────────────────────────────────────┐
  │  Thread 1 ──► GET /materia/1/                        │
  │  Thread 2 ──► GET /materia/2/          15 req/s      │
  │  ...                                  1 public IP   │
  │  Thread 15 ──► GET /materia/15/                      │
  └──────────────────────────────────────────────────────┘

  To nginx and an IP-based counter: identical.

  Resolution strategies applied:
  ┌──────────────────────────────────────────────────────────────────┐
  │  Known safe high-freq paths  → nginx bypass + Django bypass      │
  │  Authenticated users         → per-user counter (uid), NAT-safe  │
  │  Anonymous /api/             → quota only, no IP counter         │
  │  Everything else (anon)      → IP counter + 300s block on breach │
  └──────────────────────────────────────────────────────────────────┘

  Long-term:  APP_ACCESS_KEYs per tenant → quota per org, not per IP
              WebSocket push for voting  → eliminates polling bursts
```

---

## Pending Investigations

The following incidents may or may not share the same root cause as the PatoBranco-PR event. Each should be investigated using the OpenSearch query patterns established above and documented here.

- [ ] Other houses reporting intermittent 429s during session hours
- [ ] Azure crawler bot (`52.167.144.162`) — 2 × 429 observed on 2026-05-06 at patobranco-pr; appears to be a legitimate Microsoft indexer hitting non-session paths; confirm it is correctly rate-limited and not causing collateral blocks on shared IPs
- [ ] Investigate whether `187.109.99.234/30` (patobranco secondary NAT range) experienced any blocks independently of `200.175.17.66/29`
