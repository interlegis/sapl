#!/usr/bin/env bash
# update_geoip.sh — download / refresh GeoLite2-ASN.mmdb
#
# Run this script before building a new Docker image so the image bundles
# an up-to-date MaxMind ASN database.  The .mmdb binary is git-ignored;
# only this script is tracked.
#
# Usage:
#   # Option 1 — key in environment
#   MAXMIND_LICENSE_KEY=your_key bash docker/geoip/update_geoip.sh
#
#   # Option 2 — key in project .env file
#   bash docker/geoip/update_geoip.sh
#
# The script writes GeoLite2-ASN.mmdb to the same directory as itself so
# the Dockerfile COPY step can find it at docker/geoip/GeoLite2-ASN.mmdb.
#
# Suggested automation: run via a host cron job or CI pipeline step
# before triggering a docker build, e.g.:
#
#   # /etc/cron.weekly/update-sapl-geoip
#   #!/bin/bash
#   cd /path/to/sapl && bash docker/geoip/update_geoip.sh

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_FILE="$SCRIPT_DIR/GeoLite2-ASN.mmdb"

# ── Resolve the license key ────────────────────────────────────────────────
if [[ -z "${MAXMIND_LICENSE_KEY:-}" ]]; then
  # Try the project .env (two directories up from docker/geoip/)
  ENV_FILE="$(dirname "$(dirname "$SCRIPT_DIR")")/.env"
  if [[ -f "$ENV_FILE" ]]; then
    MAXMIND_LICENSE_KEY="$(grep -E '^MAXMIND_LICENSE_KEY=' "$ENV_FILE" 2>/dev/null \
      | cut -d= -f2- | tr -d '[:space:]' || true)"
  fi
fi

if [[ -z "${MAXMIND_LICENSE_KEY:-}" ]]; then
  echo "ERROR: MAXMIND_LICENSE_KEY is not set." >&2
  echo "  Set it in the environment or add MAXMIND_LICENSE_KEY=<key> to .env" >&2
  exit 1
fi

# ── Download ───────────────────────────────────────────────────────────────
URL="https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz"

echo "[geoip] Downloading GeoLite2-ASN from MaxMind..."
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

curl -fsSL --max-time 60 "$URL" | tar -xz --strip-components=1 -C "$tmpdir"
mv "$tmpdir"/GeoLite2-ASN.mmdb "$OUT_FILE"

echo "[geoip] Saved: $OUT_FILE"
echo "[geoip] Build date: $(python3 -c "
import struct, datetime, pathlib
data = pathlib.Path('$OUT_FILE').read_bytes()
# MaxMind DB build epoch is in the last 16 bytes of the metadata section
marker = b'\xab\xcd\xefMaxMind.com'
idx = data.rfind(marker)
if idx >= 0:
    # search for 'build_epoch' key nearby
    chunk = data[idx:idx+512]
    pos = chunk.find(b'build_epoch')
    if pos >= 0:
        val_start = pos + len(b'build_epoch') + 1
        epoch = struct.unpack('>Q', chunk[val_start+1:val_start+9])[0]
        print(datetime.datetime.utcfromtimestamp(epoch).strftime('%Y-%m-%d'))
        exit()
print('unknown')
" 2>/dev/null || echo "unknown")"
