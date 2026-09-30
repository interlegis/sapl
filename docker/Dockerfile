# ---------- 1) BUILDER ----------
FROM python:3.12-slim-bookworm AS builder

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    VENV_DIR=/opt/venv \
    PIP_NO_CACHE_DIR=on

# Dev headers e toolchain só no builder
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential git pkg-config \
      libpq-dev libxml2-dev libjpeg-dev libssl-dev libffi-dev libxslt1-dev \
      libcairo2-dev libpango1.0-dev libgdk-pixbuf-2.0-dev libharfbuzz-dev \
      libfreetype6-dev zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

# Venv independente do sistema
RUN python -m venv "${VENV_DIR}" \
 && "${VENV_DIR}/bin/pip" install --upgrade pip setuptools wheel

WORKDIR /build

# Copie APENAS os requirements primeiro para maximizar cache
COPY requirements/ ./requirements/

# Instale os requisitos de produção
# ATENÇÃO: se seu código importa prompt_toolkit em runtime, inclua em requirements.txt:
# prompt_toolkit>=3,<4
RUN "${VENV_DIR}/bin/pip" install -r requirements/requirements.txt

# Opcional: verificação de conflitos (falha cedo se faltar algo)
RUN "${VENV_DIR}/bin/pip" check || true


# ---------- 2) RUNTIME ----------
FROM python:3.12-slim-bookworm AS runtime

ARG WITH_GRAPHVIZ=1
ARG WITH_POPPLER=1
ARG WITH_PSQL_CLIENT=1
ARG WITH_NGINX=1

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    VENV_DIR=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PIP_NO_CACHE_DIR=on

# Pacotes de runtime (sem *-dev)
# Removi python3/python3-venv (já temos o Python da base)
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      curl jq bash tzdata fontconfig tini libmagic1 \
      libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
      libharfbuzz0b libfreetype6 libjpeg62-turbo zlib1g fonts-dejavu-core; \
    if [ "$WITH_GRAPHVIZ" = "1" ]; then apt-get install -y --no-install-recommends graphviz; fi; \
    if [ "$WITH_POPPLER" = "1" ]; then apt-get install -y --no-install-recommends poppler-utils; fi; \
    if [ "$WITH_PSQL_CLIENT" = "1" ]; then apt-get install -y --no-install-recommends postgresql-client; fi; \
    if [ "$WITH_NGINX" = "1" ]; then apt-get install -y --no-install-recommends nginx; fi; \
    rm -rf /var/lib/apt/lists/*

# Usuários/grupos (idempotente)
RUN useradd --system --no-create-home --shell /usr/sbin/nologin sapl || true \
 && groupadd -g 101 -r nginx || true \
 && usermod -aG nginx www-data || true \
 && usermod -aG nginx sapl || true

# Estrutura de diretórios
RUN mkdir -p /var/interlegis/sapl /var/interlegis/sapl/data /var/interlegis/sapl/media /var/interlegis/sapl/run \
 && chown -R root:nginx /var/interlegis/sapl /var/interlegis/sapl/run \
 && chmod -R g+rwX /var/interlegis/sapl \
 && chmod 2775 /var/interlegis/sapl /var/interlegis/sapl/run \
 && find /var/interlegis/sapl -type d -exec chmod g+s {} +

WORKDIR /var/interlegis/sapl/

# Traga o venv pré-instalado
COPY --from=builder ${VENV_DIR} ${VENV_DIR}

# Código da aplicação (depois do venv para aproveitar cache)
COPY . /var/interlegis/sapl/

# Nginx (somente se instalado)
RUN if [ "$WITH_NGINX" = "1" ]; then \
      rm -f /etc/nginx/conf.d/*; \
      cp docker/config/nginx/sapl.conf /etc/nginx/conf.d/sapl.conf; \
      cp docker/config/nginx/nginx.conf /etc/nginx/nginx.conf; \
    fi

# Scripts + gunicorn.conf no diretório da app
RUN install -m 755 docker/startup_scripts/start.sh               /var/interlegis/sapl/start.sh \
 && install -m 755 docker/startup_scripts/wait-for-pg.sh         /var/interlegis/sapl/wait-for-pg.sh \
 && install -m 755 docker/startup_scripts/wait-for-solr.sh       /var/interlegis/sapl/wait-for-solr.sh \
 && install -m 644 docker/startup_scripts/solr_cli.py            /var/interlegis/sapl/solr_cli.py \
 && install -m 644 docker/startup_scripts/create_admin.py        /var/interlegis/sapl/create_admin.py \
 && install -m 644 docker/startup_scripts/genkey.py              /var/interlegis/sapl/genkey.py \
 && install -m 644 docker/startup_scripts/gunicorn.conf.py       /var/interlegis/sapl/gunicorn.conf.py

# (Se possível, evite copiar .env no build. Use secrets/variáveis em runtime.)
COPY docker/config/env_dockerfile /var/interlegis/sapl/sapl/.env

# Logs (só se nginx estiver presente)
RUN if [ "$WITH_NGINX" = "1" ]; then \
      ln -sf /dev/stdout /var/log/nginx/access.log; \
      ln -sf /dev/stderr /var/log/nginx/error.log; \
    fi \
 && mkdir -p /var/log/sapl/ \
 && ln -sf /var/interlegis/sapl/sapl.log /var/log/sapl/sapl.log

# Cache de fontes e collectstatic
# NÃO atualizamos pip aqui (já veio pronto do builder)
RUN fc-cache -fv \
 && python manage.py collectstatic --noinput --clear \
 && rm -f /var/interlegis/sapl/sapl/.env /var/interlegis/sapl/sapl.db || true

ENV DEBIAN_FRONTEND=teletype

EXPOSE 80 443
VOLUME ["/var/interlegis/sapl/data", "/var/interlegis/sapl/media", "/var/log/sapl/"]

ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["/var/interlegis/sapl/start.sh"]
