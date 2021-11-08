FROM python:3.7-slim-buster

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1

#ENV PYTHONFAULTHANDLER 1

ENV DEBIAN_FRONTEND noninteractive

ENV BUILD_PACKAGES apt-utils apt-file libpq-dev graphviz-dev build-essential git pkg-config \
                   python3-dev libxml2-dev libjpeg-dev libssl-dev libffi-dev libxslt1-dev \
                   libcairo2-dev software-properties-common python3-setuptools python3-pip

## NAO EH PRA TIRAR O vim DA LISTA DE COMANDOS INSTALADOS!!!
ENV RUN_PACKAGES graphviz python3-lxml python3-magic postgresql-client python3-psycopg2 \
                 poppler-utils curl jq bash vim python3-venv tzdata nodejs \
                 fontconfig ttf-dejavu python nginx
 
RUN mkdir -p /var/interlegis/sapl

WORKDIR /var/interlegis/sapl/

ADD . /var/interlegis/sapl/

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends $BUILD_PACKAGES $RUN_PACKAGES && \
    fc-cache -fv && \
    pip3 install --no-cache-dir --upgrade pip setuptools && \
    rm -f /etc/nginx/conf.d/* && \
    pip install --no-cache-dir -r /var/interlegis/sapl/requirements/dev-requirements.txt --upgrade setuptools && \
    SUDO_FORCE_REMOVE=yes apt-get purge -y --auto-remove $BUILD_PACKAGES && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV HOME=/var/interlegis/sapl

COPY docker/start.sh $HOME
COPY docker/check_solr.sh $HOME
COPY docker/solr_api.py $HOME
COPY docker/busy-wait.sh $HOME
COPY docker/create_admin.py $HOME
COPY docker/genkey.py $HOME
COPY docker/gunicorn_start.sh $HOME

COPY docker/config/nginx/sapl.conf /etc/nginx/conf.d
COPY docker/config/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/config/env_dockerfile /var/interlegis/sapl/sapl/.env

RUN python3 manage.py collectstatic --noinput --clear

# Remove .env(fake) e sapl.db da imagem
RUN rm -rf /var/interlegis/sapl/sapl/.env && \
    rm -rf /var/interlegis/sapl/sapl.db

RUN chmod +x /var/interlegis/sapl/start.sh && \
    chmod +x /var/interlegis/sapl/check_solr.sh && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log && \
    mkdir /var/log/sapl/ && touch /var/interlegis/sapl/sapl.log && \
    ln -s /var/interlegis/sapl/sapl.log /var/log/sapl/sapl.log

# Debian não possui usuário 'nginx' necessário para o Debian
RUN useradd --no-create-home nginx

ENV DEBIAN_FRONTEND teletype

EXPOSE 80/tcp 443/tcp

VOLUME ["/var/interlegis/sapl/data", "/var/interlegis/sapl/media"]

CMD ["/var/interlegis/sapl/start.sh"]
