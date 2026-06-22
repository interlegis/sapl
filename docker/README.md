# SAPL Docker Build

## Building locally

### 1. Prerequisites

- Docker 23+ with BuildKit enabled (default since Docker 23)
- A free [MaxMind account](https://www.maxmind.com/en/geolite2/signup) with a license key

### 2. Set your MaxMind license key

Add the key to the project root `.env` file (already gitignored):

```
MAXMIND_LICENSE_KEY=your_key_here
```

The key is used **only at build time** to download the `GeoLite2-ASN.mmdb` database for
nginx ASN-based bot blocking. It is injected via a BuildKit secret and is **never stored
in any image layer** — it will not appear in `docker history` or any registry push.

### 3. Build the image

```bash
docker build \
  --secret id=maxmind_key,src=.env \
  -f docker/Dockerfile \
  -t sapl:local \
  .
```

Run from the **project root** (not from inside `docker/`), so the build context includes
the full source tree.

#### Optional build args

| Arg | Default | Description |
|---|---|---|
| `WITH_NGINX` | `1` | Include nginx in the image |
| `WITH_GRAPHVIZ` | `1` | Include Graphviz |
| `WITH_POPPLER` | `1` | Include Poppler (PDF utilities) |
| `WITH_PSQL_CLIENT` | `1` | Include `psql` client |

Example — build without Graphviz:

```bash
docker build \
  --secret id=maxmind_key,src=.env \
  --build-arg WITH_GRAPHVIZ=0 \
  -f docker/Dockerfile \
  -t sapl:local \
  .
```

### 4. If the MaxMind key is not provided

The build will succeed but nginx will log an error on startup because
`/etc/nginx/geoip/GeoLite2-ASN.mmdb` will be missing. ASN-based bot blocking will
be inactive. All other Phase 0 mitigations (UA blocklist, rate limits, ETags) still apply.

You can mount the database file at runtime as a workaround:

```bash
docker run \
  -v /path/to/GeoLite2-ASN.mmdb:/etc/nginx/geoip/GeoLite2-ASN.mmdb:ro \
  sapl:local
```

---

## Production — Harbor

Official images are built and pushed through **Harbor**. Before the next release, configure
the MaxMind license key as a build secret in the Harbor / CI pipeline:

1. Add `MAXMIND_LICENSE_KEY` as a **masked CI/CD secret** in the Harbor build project
   (do not put it in any Helm values file or ConfigMap).
2. Pass it to the build step:
   ```bash
   docker build \
     --secret id=maxmind_key,env=MAXMIND_LICENSE_KEY \
     -f docker/Dockerfile \
     -t harbor.your-registry/sapl/sapl:$VERSION \
     .
   ```
   Note: `env=` variant reads the secret from an environment variable instead of a file —
   useful in CI where `.env` files are not present.
3. Push as normal — the key will not be present in the pushed image.

### Keeping GeoLite2-ASN up to date

MaxMind updates the database every Tuesday. On production hosts, install the weekly refresh
cron (run as root):

```bash
cat > /etc/cron.weekly/update-geoip << 'EOF'
#!/bin/bash
MAXMIND_KEY="$(kubectl get secret sapl-build-secrets -n interlegis-infra \
  -o jsonpath='{.data.MAXMIND_LICENSE_KEY}' | base64 -d)"
curl -fsSL \
  "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=${MAXMIND_KEY}&suffix=tar.gz" \
  | tar -xz -C /tmp --wildcards '*.mmdb'
mv /tmp/GeoLite2-ASN_*/GeoLite2-ASN.mmdb /etc/nginx/geoip/GeoLite2-ASN.mmdb
nginx -s reload
EOF
chmod +x /etc/cron.weekly/update-geoip
```
