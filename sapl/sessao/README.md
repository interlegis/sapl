# Painel backed by WebSockets — manual E2E verification

This is a note about the **`feat/painel-websockets` branch** (a timeboxed
spike, forked from `fix/painel-registro-votacao-trava`), which adds live
server push (WebSockets over Redis) to the plenary-session "painel"
feature, additively on top of the existing HTTP-polling implementation.
It lives in this app's directory because the broadcast trigger points
(`abrir_votacao`, `VotacaoNominalAbstract.post`) are here in
`sapl/sessao/views.py` — the WebSocket infrastructure itself (consumer,
ASGI routing, the shared payload builder) lives in `sapl/painel/`.

If you're reading this outside that branch, most of what's described
below doesn't exist yet.

## Requirements to run this branch (local dev)

Four things need to be running at once. Order matters a little (Redis
before the Django/ASGI process; `yarn serve` before you load a page, or
its bundles 404).

1. **Redis, with persistence off** (channel layer only — nothing here
   needs to survive a restart):
   ```
   redis-server --save "" --appendonly no
   ```
   or, if you'd rather not install Redis locally:
   ```
   docker run --rm -p 6379:6379 redis:7-alpine redis-server --save "" --appendonly no
   ```
   Make sure `REDIS_URL` in `.env` actually resolves to it — it must be a
   full URL (`redis://127.0.0.1:6379/0`, matching `sapl/settings.py`'s
   default). The repo's current `.env` has `REDIS_URL=localhost:6380`,
   which is **not** in that form — if WebSocket updates silently never
   arrive, check this first before suspecting the consumer/broadcast code.

2. **Python deps** (adds `channels`/`daphne`/`channels-redis` on top of
   the usual requirements — skip if already installed):
   ```
   pip install -r requirements/dev-requirements.txt
   ```

3. **Frontend dev bundle** (the Vue pages — painel, votação nominal, voto
   individual, votação simbólica, leitura de matéria — are served via
   `{% render_bundle %}`, which in `DEBUG` mode reads
   `frontend/dev-webpack-stats.json` and points `<script>` tags at the
   dev server; without this running you'll get a template error, not a
   blank page):
   ```
   yarn install   # once
   yarn serve
   ```

4. **The Django/ASGI process itself — pick one, not both:**
   ```
   daphne -b 127.0.0.1 -p 8000 sapl.asgi:application
   ```
   or
   ```
   ./manage.py runserver
   ```
   `sapl.asgi.application` is a single ASGI app that routes **both**
   regular HTTP and `/ws/painel/<sessao_id>/` — and every WS client here
   (Vue's `main.js` files and the legacy vanilla-JS templates alike)
   opens its socket at `window.location.host`, i.e. *the same host:port
   the page was loaded from*. So this has to be one process on one port,
   not Daphne-on-one-port-plus-runserver-on-another. There's no HTTP
   polling fallback anywhere in this branch anymore — every screen here
   is WS-only (see "Architecture" below) — so a two-port setup wouldn't
   just be slower, it would leave every page permanently stuck showing a
   "conexão perdida" banner. `scripts/verify_painel_websockets.sh` runs a
   single Daphne process for exactly this reason.

   Between the two: **use Daphne when you're actively debugging the
   WebSocket itself** — its logs/errors for a failed or dropped `/ws/`
   connection are far more legible, and this is where you'll spend time
   if something in the merged backend misbehaves. Daphne does **not**
   autoreload on code changes, though, so for everyday work (editing
   views/templates, not the consumer/broadcast path) run `runserver`
   instead — Channels patches it to serve the same combined HTTP+WS app,
   just with autoreload, and you restart it far less often.

## Architecture in one paragraph

Every client screen — the three legacy vanilla-JS templates (the public
painel `sapl/templates/painel/index.html`, the tablet voting screen
`sapl/templates/painel/voto_individual.html`, the operator's
vote-registration screen `sapl/templates/sessao/votacao/nominal.html`) and
the five Vue v2 pages (painel, votação nominal, voto individual, votação
simbólica, leitura de matéria) — open a WebSocket to
`/ws/painel/<sessao_id>/` (one Channels group per `SessaoPlenaria`,
`sapl/painel/consumers.py::PainelConsumer`) and get a full state snapshot
immediately on connect (`PainelConsumer.connect()` sends one right after
`accept()` — this is what makes a page reload or a reconnect self-heal
with no gap, instead of showing stale data until the next event).
Whenever a view mutates presença, orador, vote, or matéria state, it calls
`broadcast_dados_painel(request, sessao_id)` (`sapl/painel/views.py`),
which re-runs `build_dados_painel()` and publishes the full payload to
that group over Redis (`channels_redis`). Every connected client gets the
*same* full-state payload; there is no separate delta format.

**There is no HTTP polling fallback anywhere in this branch.** Every
screen listed above is WS-only: if the socket drops, nothing updates
until it reconnects. Each screen's JS shows a visible banner
(`#ws-status-banner` in the legacy templates, `<ws-status-banner>` in the
Vue pages) whenever the connection isn't open, and reconnects with an
exponential backoff (1s → 30s cap, ±30% jitter to avoid every connected
tablet retrying in lockstep). The consumer closes with a specific code for
conditions a retry can't fix — 4401 (not authenticated), 4403 (not
authorized), 4404 (no such sessão) — and the client shows a permanent
error for those instead of retrying forever. Because polling is gone,
every write path that changes anything in this payload has to call
`broadcast_dados_painel()` itself — `PresencaView`/`PresencaOrdemDiaView`,
the `Orador*Crud` create/update/delete views (via
`BroadcastPainelOnSaveMixin` in `sapl/sessao/views.py`),
`LeituraEmBloco`, and `VotacaoEmBlocoSimbolicaView`/
`VotacaoEmBlocoNominalView` were all missing this until it was added
alongside the polling removal — before that, polling was quietly masking
the gap (500ms–3s of staleness, not "never updates").

## Running it (for humans)

```
scripts/verify_painel_websockets.sh
```

This starts Redis and a single Daphne process (HTTP pages + WebSocket, one
port, one process — see the "two things need to be running" note above)
together, waits for both to actually be listening, and tails their logs
in one terminal. Ctrl+C stops and cleans up both. See the script's header
comment for port-override env vars if 6379/8002 collide with something
else on your machine.

Once it's up:

1. **Seed test data** (there's no fixture for this yet — a `manage.py
   shell` one-liner is the fastest path; see the Python snippet in the
   next section, "For LLMs / scripted setup", which works equally well
   pasted into a human's `shell` session).
2. Open the **public painel** at `http://127.0.0.1:8002/painel-principal/<sessao_id>`
   in one tab.
3. Log in as the seeded voter and open
   `http://127.0.0.1:8002/voto-individual/` in another tab (or a private
   window, since it's a different session).
4. Cast or change the vote on the voter tab. **The painel tab should
   update without a page reload**, and there should be no delay beyond
   normal network latency — that's the only path there is now. Watch the
   daphne log (tailed in the same terminal) for the connection and any
   errors.
5. To confirm the error banner actually shows up when it should (not just
   that push works): kill daphne (its pid is printed by the script) while
   the painel tab stays open. Within a few seconds every open tab should
   show the red/amber "conexão perdida" banner
   (`#ws-status-banner`/`<ws-status-banner>` — see "Architecture" above)
   instead of silently going stale.
6. To confirm reconnect: restart the script (or just daphne) while the
   painel tab stays open. Within a few seconds (backoff-dependent) the
   tab should reconnect, the banner should disappear, and the tab should
   resume live updates — check the browser console for the `WebSocket`
   connect/close log lines.

The operator's registration screen
(`sapl/sessao:votacaonominal`, URL `/sessao/<pk>/matordemdia/votnom/<oid>/<mid>`)
follows the same pattern — open it as a third tab, logged in as a user
with `sessao` module permissions, and confirm the same instant-update
behavior when a vote is registered from either the operator or the
tablet side.

## For LLMs / scripted setup

Minimal data needed for a Nominal vote to be votable end-to-end (run via
`python manage.py shell`, from the repo root, with `DJANGO_SETTINGS_MODULE=sapl.settings`):

```python
from model_bakery import baker
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from sapl.base.models import AppConfig as ConfiguracoesAplicacao
from sapl.parlamentares.models import Legislatura, SessaoLegislativa, Mandato, Parlamentar, Votante
from sapl.sessao.models import SessaoPlenaria, TipoSessaoPlenaria, OrdemDia, PresencaOrdemDia
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa

User = get_user_model()

# ConfiguracoesAplicacao.mostrar_voto controls whether the painel shows
# real vote values or masks them as "Voto Informado" before the matéria
# closes — set True to see real values live.
cfg, _ = ConfiguracoesAplicacao.objects.get_or_create(pk=1)
cfg.mostrar_voto = True
cfg.save()

legislatura = baker.make(Legislatura)
sessao_legislativa = baker.make(SessaoLegislativa)
tipo = baker.make(TipoSessaoPlenaria)
sessao = baker.make(SessaoPlenaria, legislatura=legislatura, sessao_legislativa=sessao_legislativa,
                    tipo=tipo, numero=1, iniciada=True, finalizada=False, painel_aberto=True)

materia = baker.make(MateriaLegislativa, tipo=baker.make(TipoMateriaLegislativa))
ordem = baker.make(OrdemDia, sessao_plenaria=sessao, materia=materia,
                   tipo_votacao=2, votacao_aberta=True, registro_aberto=False)  # 2 = Nominal

parlamentar = baker.make(Parlamentar, ativo=True)
baker.make(PresencaOrdemDia, sessao_plenaria=sessao, parlamentar=parlamentar)
# get_presentes() (sapl/painel/views.py, backed by sessao_presencas_view)
# only includes parlamentares with a Mandato for the session's legislatura
# — without this row the parlamentar silently never shows as "presente".
baker.make(Mandato, parlamentar=parlamentar, legislatura=legislatura,
          data_inicio_mandato=sessao.data_inicio)

# A strong password is required — SAPL's CheckWeakPasswordMiddleware
# force-redirects any login with a weak one (e.g. "x", "test") to
# /sistema/alterar-senha/ before it ever reaches the view you're testing.
# This silently breaks any requests-based scripted login otherwise.
votante_user = User.objects.create_user(username='verify-votante', password='Xk9#mQ2vLp8zR4wT!')
votante_user.user_permissions.add(Permission.objects.get(codename='can_vote'))
baker.make(Votante, parlamentar=parlamentar, user=votante_user)

print('sessao_id =', sessao.pk, '| ordem_id =', ordem.pk, '| materia_id =', materia.pk)
```

Permission model for `/ws/painel/<sessao_id>/` (`PainelConsumer.connect()`,
`sapl/painel/consumers.py`) — the connection is accepted if the
authenticated user satisfies **any** of the three permission gates the
three HTTP screens already use individually (there's no single unified
permission for this endpoint because the three source screens never had
one either):
- `user.has_module_perms('painel')` — same as `check_permission()`'s gate.
- `user.has_perm('parlamentares.can_vote')` — same as `votante_view`'s gate.
- `user.has_module_perms('sessao')` — same as the operator screen's
  `SessaoPermissionMixin` gate.

Unauthenticated connections close with code `4401`; authenticated but
unauthorized close with `4403`; a nonexistent `sessao_id` closes with
`4404` (all handled explicitly — no uncaught exceptions on bad input,
unlike the `feat/painel-votacao-v2` reference this was ported from).

To verify the broadcast path without a browser at all (what
`sapl/painel/tests/test_broadcasts.py` does, and what was used to
smoke-test this against real Redis+daphne+runserver during development):
connect with the `websockets` Python package
(`pip install websockets`, not in project requirements — it's a
verification tool, not a runtime dependency) against
`ws://127.0.0.1:8002/ws/painel/<sessao_id>/`, sending the Django
`sessionid`/`csrftoken` cookies from a `requests.Session()` that logged in
via `/login/` — then POST a vote via `requests` and confirm the socket
receives a `{"type": "data", "payload": {...}}` message with the updated
`presentes[].voto`.

## Known caveats

- **`cronometro_painel`'s "which session is this for" resolution is
  fragile.** It broadcasts to whichever `SessaoPlenaria` currently has
  `painel_aberto=True`, via `.first()` — correct under the intended
  single-open-session workflow, but nothing enforces "at most one" for
  `painel_aberto` the way `votacao_aberta` already has a DB
  `UniqueConstraint`. If more than one session has that flag set (stale
  dev data, or a real multi-tenant edge case), the broadcast goes to an
  arbitrary one of them. Not hit in practice during this spike's testing,
  but worth hardening before this goes further.
- **This is a spike, not a finished feature.** Test coverage exists
  (`sapl/painel/tests/test_consumers.py`, `test_broadcasts.py`, plus the
  Postgres-view equivalence tests in `test_votacao_nominal.py`/`tests.py`)
  and the vote/close/open/cronômetro broadcast paths were each verified
  against real infrastructure (not just the in-memory test layer) during
  development — but things like production replica count / Redis HA,
  and a nginx-level rate-limit exemption for the `/ws/` path if
  `feat/rate-limiter-2026`'s Lua layer ever merges, haven't been
  addressed here.
- **Requirements**: `channels==3.0.3`, `daphne==3.0.2`,
  `channels-redis==3.4.1`, `asgiref==3.7.2` are pinned in
  `requirements/requirements.txt` — this specific combination is the
  newest one compatible with this project's Django pin (`2.2.28`;
  Channels 4.x needs Django ≥ 4.2, out of scope for this branch).
- **Removed as dead code when polling was removed**:
  `painel_mensagem`/`painel_parlamentar`/`painel_votacao` (views, URLs,
  and their templates `painel/mensagem.html`/`parlamentares.html`/
  `votacao.html`) were an older, unrelated multi-page painel UI with no
  references anywhere else in the codebase — deleted outright rather than
  converted. `sapl.painel:dados_painel` (`get_dados_painel`) and its ETag
  helper (`_dados_painel_etag`) were also removed once nothing polled
  them anymore, along with the tests that pinned their HTTP-specific
  behavior (ETag/304, payload shape, masking) in
  `sapl/painel/tests/tests.py` — `build_dados_painel()` itself (what both
  used internally) is untouched and still backs every WS broadcast.
