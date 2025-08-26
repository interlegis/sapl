FROM python:3.12-slim-bookworm

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND noninteractive

ENV BUILD_PACKAGES="apt-utils apt-file libpq-dev graphviz-dev build-essential git pkg-config \
                    python3-dev libxml2-dev libjpeg-dev libssl-dev libffi-dev libxslt1-dev \
                    libcairo2-dev libpango1.0-dev libgdk-pixbuf-2.0-dev libharfbuzz-dev \
                    libfreetype6-dev zlib1g-dev software-properties-common python3-setuptools python3-pip"

## NAO EH PRA TIRAR O vim DA LISTA DE COMANDOS INSTALADOS!!!
ENV RUN_PACKAGES="graphviz python3-lxml python3-magic postgresql-client \
                  poppler-utils curl jq bash vim python3-venv tzdata nodejs \
                  fontconfig python3 nginx tini git \
                  libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
                  libharfbuzz0b libfreetype6 libjpeg62-turbo zlib1g fonts-dejavu-core"

## Update apt-get
RUN apt-get update \
 && apt-get install -y --no-install-recommends $BUILD_PACKAGES $RUN_PACKAGES

# Create users and groups
RUN useradd --system --no-create-home --shell /usr/sbin/nologin sapl || true \
 && groupadd -r nginx || true \
 && usermod -aG nginx www-data || true \
 && usermod -aG nginx sapl || true

# create base directories and setup access
RUN mkdir -p /var/interlegis/sapl /var/interlegis/sapl/data /var/interlegis/sapl/media /var/interlegis/sapl/run/ \
 && chown -R root:nginx /var/interlegis/sapl /var/interlegis/sapl/run/ \
 && chmod -R g+rwX /var/interlegis/sapl \
 && chmod 2775 /var/interlegis/sapl /var/interlegis/sapl/run/ \
 && find /var/interlegis/sapl -type d -exec chmod g+s {} +

# Copy app code
WORKDIR /var/interlegis/sapl/
COPY . /var/interlegis/sapl/

RUN rm -f /etc/nginx/conf.d/*
COPY docker/config/nginx/sapl.conf /etc/nginx/conf.d/
COPY docker/config/nginx/nginx.conf /etc/nginx/nginx.conf

COPY docker/startup_scripts/start.sh $HOME
COPY docker/startup_scripts/solr_cli.py $HOME
COPY docker/startup_scripts/wait-for-pg.sh $HOME
COPY docker/startup_scripts/wait-for-solr.sh $HOME
COPY docker/startup_scripts/create_admin.py $HOME
COPY docker/startup_scripts/genkey.py $HOME
COPY docker/startup_scripts/gunicorn.conf.py $HOME

COPY docker/config/nginx/sapl.conf /etc/nginx/conf.d
COPY docker/config/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/config/env_dockerfile /var/interlegis/sapl/sapl/.env

RUN chmod +x /var/interlegis/sapl/start.sh \
    && chmod +x /var/interlegis/sapl/wait-for-solr.sh \
    && chmod +x /var/interlegis/sapl/wait-for-pg.sh \
    && chmod +x /var/interlegis/sapl/start.sh \
    && chmod +x /var/interlegis/sapl/wait-for-solr.sh \
    && chmod +x /var/interlegis/sapl/wait-for-pg.sh

RUN ln -sf /dev/stdout /var/log/nginx/access.log \
 && ln -sf /dev/stderr /var/log/nginx/error.log \
 && mkdir -p /var/log/sapl/ \
 && ln -sf /var/interlegis/sapl/sapl.log /var/log/sapl/sapl.log

RUN fc-cache -fv \
 && python -m pip install --no-cache-dir --upgrade pip setuptools \
 && python -m pip install --no-cache-dir -r requirements/dev-requirements.txt


RUN apt-get purge -y --auto-remove $BUILD_PACKAGES \
 && apt-get autoremove -y \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN python manage.py collectstatic --noinput --clear

RUN rm -f /var/interlegis/sapl/sapl/.env /var/interlegis/sapl/sapl.db || true

ENV DEBIAN_FRONTEND=teletype

EXPOSE 80 443
VOLUME ["/var/interlegis/sapl/data", "/var/interlegis/sapl/media", "/var/log/sapl/"]

# tini as PID 1 so signals/zombies are handled
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["/var/interlegis/sapl/start.sh"]
