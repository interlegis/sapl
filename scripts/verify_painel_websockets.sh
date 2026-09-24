#!/usr/bin/env bash
#
# Starts the two processes needed for manual end-to-end verification of the
# painel (branch feat/painel-websockets): Redis, and a single Daphne process
# serving sapl.asgi:application — which routes both regular HTTP (page
# renders, the views that call broadcast_dados_painel()) and
# /ws/painel/<sessao_id>/ on the SAME port.
#
# This used to run Daphne and `manage.py runserver` on two separate ports.
# That doesn't work anymore: every screen this branch ships (the public
# painel, voto individual, votação nominal, and the Vue v2 pages) connects
# its WebSocket to `window.location.host` — the same host:port the page was
# loaded from — and none of them fall back to HTTP polling if that socket
# never connects. Two ports means the WS connection from a page loaded off
# the runserver port always fails, silently, with no way to notice.
#
# See sapl/sessao/README.md for what to actually click through once this is
# running, and for the daphne-vs-runserver tradeoff during regular dev.
#
# Usage: scripts/verify_painel_websockets.sh
# Stop everything with Ctrl+C.
#
# Ports are overridable via env vars if you need to avoid a clash:
#   REDIS_PORT=6380 APP_PORT=8102 scripts/verify_painel_websockets.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

REDIS_PORT="${REDIS_PORT:-6379}"
APP_PORT="${APP_PORT:-8002}"
REDIS_URL="redis://127.0.0.1:${REDIS_PORT}/0"

LOG_DIR="$(mktemp -d /tmp/painel-ws-verify.XXXXXX)"
REDIS_LOG="$LOG_DIR/redis.log"
APP_LOG="$LOG_DIR/daphne.log"

REDIS_PID=""
APP_PID=""
TAIL_PID=""

log() { echo -e "\033[36m[verify]\033[0m $*"; }
err() { echo -e "\033[31m[verify]\033[0m $*" >&2; }

port_in_use() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "'$1' not found on PATH. Activate the project's virtualenv first."
    exit 1
  fi
}

require_port_free() {
  local port="$1" label="$2"
  if port_in_use "$port"; then
    err "Port $port is already in use (needed for $label)."
    err "Find what's on it: lsof -nP -iTCP:$port -sTCP:LISTEN"
    exit 1
  fi
}

wait_for_tcp() {
  local port="$1" label="$2" timeout="${3:-15}" waited=0
  while ! port_in_use "$port"; do
    sleep 0.5
    waited=$((waited + 1))
    if (( waited >= timeout * 2 )); then
      err "$label did not start listening on port $port within ${timeout}s."
      err "Check the logs in $LOG_DIR"
      cleanup
      exit 1
    fi
  done
}

cleanup() {
  trap - EXIT INT TERM
  log "Stopping..."
  [[ -n "$TAIL_PID" ]] && kill "$TAIL_PID" 2>/dev/null || true
  [[ -n "$APP_PID" ]] && kill "$APP_PID" 2>/dev/null || true
  [[ -n "$REDIS_PID" ]] && kill "$REDIS_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  log "Stopped. Logs kept at $LOG_DIR"
}
trap cleanup EXIT INT TERM

require_cmd lsof
require_cmd redis-server
require_cmd redis-cli
require_cmd daphne

require_port_free "$REDIS_PORT" redis-server
require_port_free "$APP_PORT" daphne

log "Logs: $LOG_DIR"

log "Starting redis-server on port $REDIS_PORT..."
redis-server --port "$REDIS_PORT" --save "" --appendonly no >"$REDIS_LOG" 2>&1 &
REDIS_PID=$!
wait_for_tcp "$REDIS_PORT" redis-server
redis-cli -p "$REDIS_PORT" ping >/dev/null 2>&1 || {
  err "redis-server started but is not responding to PING — check $REDIS_LOG"
  exit 1
}
log "redis-server ready (pid $REDIS_PID)."

log "Starting daphne (HTTP + WebSocket, one process) on 127.0.0.1:$APP_PORT ..."
(
  cd "$PROJECT_DIR"
  REDIS_URL="$REDIS_URL" exec daphne -b 127.0.0.1 -p "$APP_PORT" sapl.asgi:application
) >"$APP_LOG" 2>&1 &
APP_PID=$!
wait_for_tcp "$APP_PORT" daphne
log "daphne ready (pid $APP_PID)."

cat <<EOF

$(printf '\033[32mBoth processes are up.\033[0m')

  App (HTTP pages + WebSocket, same port): http://127.0.0.1:$APP_PORT/
  Redis:                                    127.0.0.1:$REDIS_PORT

See sapl/sessao/README.md for what to click through and test accounts/data.
There's no HTTP-polling fallback on any of these screens — if a page never
updates, check this terminal's daphne log for a WebSocket close/error first.

Press Ctrl+C to stop both.

EOF

log "Tailing logs (Ctrl+C to stop everything)..."
tail -n +1 -f "$REDIS_LOG" "$APP_LOG" &
TAIL_PID=$!
wait "$TAIL_PID"
