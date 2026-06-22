#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

APP_DIR="/var/interlegis/sapl"
DATA_DIR="/var/interlegis/sapl/data"
RUN_DIR="/var/interlegis/sapl/run"

ENV_FILE="$APP_DIR/.env"
SECRET_FILE="$DATA_DIR/secret.key"

chown -R root:nginx "$RUN_DIR" || true
chmod -R g+rwX "$RUN_DIR" || true

# setgid bit on our writable trees (not data/)
find "$RUN_DIR" -type d -exec chmod g+s {} + 2>/dev/null || true

log() { printf '[%s] %s\n' "$(date -Is)" "$*"; }
err() { printf '[%s] ERROR: %s\n' "$(date -Is)" "$*" >&2; }

cleanup() { jobs -p | xargs -r kill 2>/dev/null || true; }
trap cleanup TERM INT EXIT

# --- new function ---
configure_pg_timezone() {
  : "${DATABASE_URL:=postgresql://sapl:sapl@sapldb:5432/sapl}"
  : "${DB_TIMEZONE:=America/Sao_Paulo}"
  : "${DB_NAME:=}"
  : "${DB_ROLE:=}"

  log "Checking database/role timezone defaults…"

  # Detect DB and role if not provided
  if [[ -z "$DB_NAME" ]]; then
    DB_NAME="$(psql "$DATABASE_URL" -At -v ON_ERROR_STOP=1 -c 'select current_database();')"
  fi
  if [[ -z "$DB_ROLE" ]]; then
    DB_ROLE="$(psql "$DATABASE_URL" -At -v ON_ERROR_STOP=1 -c 'select current_user;')"
  fi

  # What is the effective timezone for this DB/role right now?
  current_tz="$(psql "$DATABASE_URL" -At -v ON_ERROR_STOP=1 -c 'show time zone;')"
  current_tz_lower="${current_tz,,}"

  # Consider these as already UTC
  if [[ "$current_tz_lower" == "utc" || "$current_tz_lower" == "etc/utc" ]]; then
    log "Timezone already UTC for DB='$DB_NAME' ROLE='$DB_ROLE' (SHOW TIME ZONE => $current_tz). Skipping ALTERs."
    return
  fi

  log "Timezone is '$current_tz' (not UTC). Applying persistent defaults…"

  # Persist at database level (requires DB owner or superuser)
  if psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q \
      -c "ALTER DATABASE \"$DB_NAME\" SET timezone TO '$DB_TIMEZONE';"; then
    log "ALTER DATABASE \"$DB_NAME\" SET timezone TO '$DB_TIMEZONE' applied."
  else
    err "ALTER DATABASE \"$DB_NAME\" failed. Need DB owner or superuser."
    exit 1
  fi

  # Persist at role level (requires superuser)
  if psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q \
      -c "ALTER ROLE \"$DB_ROLE\" SET timezone TO '$DB_TIMEZONE';"; then
    log "ALTER ROLE \"$DB_ROLE\" SET timezone TO '$DB_TIMEZONE' applied."
  else
    err "ALTER ROLE \"$DB_ROLE\" failed. Need superuser privileges."
    exit 1
  fi

  # Re-check (new session shows the new default)
  verify_tz="$(psql "$DATABASE_URL" -At -v ON_ERROR_STOP=1 -c 'show time zone;')"
  log "SHOW TIME ZONE now => $verify_tz (new sessions will inherit the defaults)."
}


create_secret() {
  if [[ -f "$SECRET_FILE" ]]; then
    SECRET_KEY="$(<"$SECRET_FILE")"
  else
    log "Generating SECRET_KEY..."
    SECRET_KEY="$(python3 genkey.py)"
    umask 177
    printf '%s\n' "$SECRET_KEY" > "$SECRET_FILE"
  fi
  export SECRET_KEY
}

write_env_file() {
  : "${DATABASE_URL:=postgresql://sapl:sapl@sapldb:5432/sapl}"
  : "${DEBUG:=False}"
  : "${EMAIL_USE_TLS:=True}"
  : "${EMAIL_PORT:=587}"
  : "${EMAIL_HOST:=}"
  : "${EMAIL_HOST_USER:=}"
  : "${EMAIL_HOST_PASSWORD:=}"
  : "${DEFAULT_FROM_EMAIL:=$EMAIL_HOST_USER}"
  : "${SERVER_EMAIL:=$EMAIL_HOST_USER}"
  : "${USE_SOLR:=False}"
  : "${SOLR_COLLECTION:=sapl}"
  : "${SOLR_URL:=http://localhost:8983}"
  : "${IS_ZK_EMBEDDED:=False}"
  : "${NUM_SHARDS:=1}"
  : "${RF:=1}"
  : "${MAX_SHARDS_PER_NODE:=1}"
  : "${ENABLE_SAPN:=False}"
  : "${REDIS_URL:=}"
  : "${CACHE_BACKEND:=file}"
  : "${POD_NAMESPACE:=sapl}"
  # nginx burst defaults — 2× each zone's sustained rate.
  # general=90r/m  media=180r/m  api=60r/m  heavy=10r/m
  : "${NGINX_BURST_GENERAL:=180}"
  : "${NGINX_BURST_MEDIA:=180}"
  : "${NGINX_BURST_API:=120}"
  : "${NGINX_BURST_HEAVY:=20}"
  export NGINX_BURST_GENERAL NGINX_BURST_MEDIA NGINX_BURST_API NGINX_BURST_HEAVY

  tmp="$(mktemp)"
  {
    printf 'SECRET_KEY=%s\n' "$SECRET_KEY"
    printf 'DATABASE_URL=%s\n' "$DATABASE_URL"
    printf 'DEBUG=%s\n' "$DEBUG"
    printf 'EMAIL_USE_TLS=%s\n' "$EMAIL_USE_TLS"
    printf 'EMAIL_PORT=%s\n' "$EMAIL_PORT"
    printf 'EMAIL_HOST=%s\n' "$EMAIL_HOST"
    printf 'EMAIL_HOST_USER=%s\n' "$EMAIL_HOST_USER"
    printf 'EMAIL_HOST_PASSWORD=%s\n' "$EMAIL_HOST_PASSWORD"
    printf 'EMAIL_SEND_USER=%s\n' "$EMAIL_HOST_USER"
    printf 'DEFAULT_FROM_EMAIL=%s\n' "$DEFAULT_FROM_EMAIL"
    printf 'SERVER_EMAIL=%s\n' "$SERVER_EMAIL"
    printf 'USE_SOLR=%s\n' "$USE_SOLR"
    printf 'SOLR_COLLECTION=%s\n' "$SOLR_COLLECTION"
    printf 'SOLR_URL=%s\n' "$SOLR_URL"
    printf 'IS_ZK_EMBEDDED=%s\n' "$IS_ZK_EMBEDDED"
    printf 'NUM_SHARDS=%s\n' "$NUM_SHARDS"
    printf 'RF=%s\n' "$RF"
    printf 'MAX_SHARDS_PER_NODE=%s\n' "$MAX_SHARDS_PER_NODE"
    printf 'ENABLE_SAPN=%s\n' "$ENABLE_SAPN"
    printf 'REDIS_URL=%s\n' "$REDIS_URL"
    printf 'CACHE_BACKEND=%s\n' "$CACHE_BACKEND"
    printf 'POD_NAMESPACE=%s\n' "$POD_NAMESPACE"
    printf 'NGINX_BURST_GENERAL=%s\n' "$NGINX_BURST_GENERAL"
    printf 'NGINX_BURST_MEDIA=%s\n' "$NGINX_BURST_MEDIA"
    printf 'NGINX_BURST_API=%s\n' "$NGINX_BURST_API"
    printf 'NGINX_BURST_HEAVY=%s\n' "$NGINX_BURST_HEAVY"
  } > "$tmp"

  chmod 600 "$tmp"
  mv -f "$tmp" "$ENV_FILE"
  log "[ENV] wrote $ENV_FILE"
}

wait_for_pg() {
  : "${DATABASE_URL:=postgresql://sapl:sapl@sapldb:5432/sapl}"
  export DATABASE_URL
  log "Waiting for Postgres..."
  /bin/bash wait-for-pg.sh "$DATABASE_URL"
}

migrate_db() {
  log "Running Django migrations..."
  python3 manage.py migrate --noinput
}

# In start.sh (near your other helpers)
configure_solr() {
  # respect envs, with sane defaults
  local USE="${USE_SOLR:-False}"
  local URL="${SOLR_URL:-http://admin:solr@localhost:8983}"
  local COL="${SOLR_COLLECTION:-sapl}"
  local SHARDS="${NUM_SHARDS:-1}"
  local RF="${RF:-1}"
  local MS="${MAX_SHARDS_PER_NODE:-1}"
  local IS_ZK="${IS_ZK_EMBEDDED:-False}"

  # total wait time before we give up (seconds)
  local WAIT_TIMEOUT="${SOLR_WAIT_TIMEOUT:-30}"
  # per probe max seconds
  local PROBE_TIMEOUT="${SOLR_PROBE_TIMEOUT:-3}"
  # sleep between probes
  local SLEEP_SECS="${SOLR_WAIT_INTERVAL:-2}"

  # feature flag OFF by default unless we confirm Solr
  ./manage.py waffle_switch SOLR_SWITCH off --create || true

  # Fast exit if disabled
  if [[ "${USE,,}" != "true" ]]; then
    echo "[SOLR] USE_SOLR=$USE → skipping Solr initialization."
    return 0
  fi

  echo "[SOLR] Best-effort wait (<= ${WAIT_TIMEOUT}s): $URL, collection=$COL"

  local deadline=$((SECONDS + WAIT_TIMEOUT))
  while (( SECONDS < deadline )); do
    # Try a cheap SolrCloud endpoint; swap for /solr/admin/info/system if you prefer
    if curl -fsS --max-time "${PROBE_TIMEOUT}" \
         "${URL%/}/solr/admin/collections?action=LIST" >/dev/null; then
      echo "[SOLR] Reachable. Kicking off background configuration…"

      # optional flag if ZK is embedded
      local ZK_FLAG=""
      if [[ "${IS_ZK,,}" == "true" ]]; then
        ZK_FLAG="--embedded_zk"
      fi

      (
        set -Eeuo pipefail
        python3 solr_cli.py \
          -u "$URL" -c "$COL" -s "$SHARDS" -rf "$RF" -ms "$MS" $ZK_FLAG
        ./manage.py waffle_switch SOLR_SWITCH on --create
        echo "[SOLR] Configuration done, SOLR_SWITCH=on."
      ) >/var/log/sapl/solr_init.log 2>&1 & disown

      return 0
    fi
    sleep "${SLEEP_SECS}"
  done

  echo "[SOLR] Not reachable within ${WAIT_TIMEOUT}s. Proceeding without Solr (SOLR_SWITCH=off)."
  return 0
}

configure_sapn() {
  if [[ "${ENABLE_SAPN,,}" == "true" ]]; then
    log "Enabling SAPN"
    python3 manage.py waffle_switch SAPN_SWITCH on --create
  else
    log "Disabling SAPN"
    python3 manage.py waffle_switch SAPN_SWITCH off --create
  fi
}

create_admin() {
  log "Creating admin user..."
  out="$(python3 create_admin.py 2>&1 || true)"
  printf '%s\n' "$out"

  if grep -q 'MISSING_ADMIN_PASSWORD' <<<"$out"; then
    err "[SUPERUSER] ADMIN_PASSWORD not set. Exiting."
    exit 1
  fi
}

fix_logging_and_socket_perms() {
  local APP_DIR="/var/interlegis/sapl"
  local LOG_FILE="$APP_DIR/sapl.log"

  # dirs
  mkdir -p "$APP_DIR/run"
  chmod 2775 "$APP_DIR/run"

  # new files/sockets → 660
  umask 0007

  # ensure log file is owned by sapl and writable
  install -Dm0660 /dev/null "$LOG_FILE"
  chown sapl:nginx "$LOG_FILE"

  # stale socket cleanup (if any)
  rm -f "$APP_DIR/run/gunicorn.sock" 2>/dev/null || true
}

setup_cache_dir() {
  # if you later move cache under /var/interlegis/sapl/cache, this line can read an env var
  local CACHE_DIR="${DJANGO_CACHE_DIR:-/var/tmp/django_cache}"

  mkdir -p "$CACHE_DIR"
  chown -R sapl:nginx "$CACHE_DIR"
  chmod -R 2775 "$CACHE_DIR"
  find "$CACHE_DIR" -type d -exec chmod g+s {} +

  # keep your global umask; 0007 ensures new files are rw for owner+group
  umask 0007
}

# ---------------------------------------------------------------------------
# Tenant namespace — resolved once at startup, written into .env
# ---------------------------------------------------------------------------

resolve_pod_namespace() {
  # 1. Already set by K8s Downward API (fieldRef: metadata.namespace)
  [[ -n "${POD_NAMESPACE:-}" ]] && { log "POD_NAMESPACE=${POD_NAMESPACE} (from env)."; return 0; }

  # 2. K8s service-account namespace file (present in every in-cluster pod)
  local ns_file="/var/run/secrets/kubernetes.io/serviceaccount/namespace"
  if [[ -f "$ns_file" ]]; then
    export POD_NAMESPACE="$(<"$ns_file")"
    log "POD_NAMESPACE=${POD_NAMESPACE} (from service-account file)."
    return 0
  fi

  # 3. Fallback for local development
  export POD_NAMESPACE="sapl"
  log "POD_NAMESPACE not found — using fallback '${POD_NAMESPACE}'."
}

# ---------------------------------------------------------------------------
# Redis — check URL from deployment env, waffle switch, connectivity
# ---------------------------------------------------------------------------

# 1. Log whether REDIS_URL was provided via the deployment env.
resolve_redis_url() {
  if [[ -n "${REDIS_URL:-}" ]]; then
    log "REDIS_URL set: $REDIS_URL"
  else
    log "REDIS_URL not set — file-based cache will be used."
  fi
}

# 2. Create/reset the REDIS_CACHE waffle switch; set CACHE_BACKEND accordingly.
configure_redis_cache() {
  ./manage.py waffle_switch REDIS_CACHE off --create || true
  if [[ -z "${REDIS_URL:-}" ]]; then
    log "REDIS_URL not set — REDIS_CACHE switch OFF."
    return 0
  fi
  ./manage.py waffle_switch REDIS_CACHE on --create || true
  export CACHE_BACKEND="redis"
  log "REDIS_URL set — REDIS_CACHE switch ON."
}

# 4. Block until Redis is reachable (or give up gracefully).
wait_for_redis() {
  [[ -z "${REDIS_URL:-}" ]] && return 0
  [[ "${CACHE_BACKEND:-file}" != "redis" ]] && return 0
  log "Checking Redis connectivity..."
  local host port retries=10
  host=$(python3 -c "from urllib.parse import urlparse; u=urlparse('${REDIS_URL}'); print(u.hostname or 'localhost')")
  port=$(python3 -c "from urllib.parse import urlparse; u=urlparse('${REDIS_URL}'); print(u.port or 6379)")
  until python3 -c "import socket; s=socket.create_connection(('$host',$port),2); s.close()" 2>/dev/null; do
    retries=$((retries - 1))
    if [[ $retries -eq 0 ]]; then
      log "WARNING: Redis unreachable after retries — falling back to file cache."
      export CACHE_BACKEND="file"
      return 0
    fi
    log "Waiting for Redis at $host:$port... ($retries retries left)"
    sleep 2
  done
  log "Redis reachable at $host:$port."
}

start_services() {
  log "Starting gunicorn..."
  gunicorn -c gunicorn.conf.py &
  log "Applying nginx config (burst: general=${NGINX_BURST_GENERAL} media=${NGINX_BURST_MEDIA} api=${NGINX_BURST_API} heavy=${NGINX_BURST_HEAVY})..."
  envsubst '${NGINX_BURST_GENERAL} ${NGINX_BURST_MEDIA} ${NGINX_BURST_API} ${NGINX_BURST_HEAVY}' \
    < /etc/nginx/conf.d/sapl.conf.template \
    > /etc/nginx/conf.d/sapl.conf
  log "Starting nginx..."
  exec /usr/sbin/nginx -g "daemon off;"
}

main() {
  create_secret
  resolve_pod_namespace
  resolve_redis_url
  wait_for_pg
  configure_pg_timezone
  migrate_db
  configure_redis_cache
  wait_for_redis
  write_env_file          # writes resolved REDIS_URL + CACHE_BACKEND into .env
  configure_solr || true
  configure_sapn
  create_admin
  setup_cache_dir
  fix_logging_and_socket_perms

  cat <<'BANNER'
-------------------------------------
| ███████╗ █████╗ ██████╗ ██╗       |
| ██╔════╝██╔══██╗██╔══██╗██║       |
| ███████╗███████║██████╔╝██║       |
| ╚════██║██╔══██║██╔═══╝ ██║       |
| ███████║██║  ██║██║     ███████╗  |
| ╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝  |
-------------------------------------
BANNER

  start_services
}

main "$@"
