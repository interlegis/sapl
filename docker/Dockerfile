FROM alpine:3.8

ENV BUILD_PACKAGES postgresql-dev graphviz-dev graphviz build-base git pkgconfig \
                   python3-dev libxml2-dev jpeg-dev libressl-dev libffi-dev libxslt-dev \
                   nodejs py3-lxml py3-magic postgresql-client poppler-utils antiword \
                   curl jq openssh-client vim bash

RUN apk update --update-cache && apk upgrade && \
    apk add --update --no-cache $BUILD_PACKAGES

RUN apk --update add fontconfig ttf-dejavu && fc-cache -fv

RUN apk add --no-cache python3 nginx tzdata && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache && \
    rm -f /etc/nginx/conf.d/*

RUN mkdir -p /var/interlegis/sapl && mkdir /var/log/sapl
WORKDIR /var/interlegis/sapl/
COPY . /var/interlegis/sapl/
RUN pip install -r /var/interlegis/sapl/requirements/dev-requirements.txt --upgrade setuptools && \
    rm -r /root/.cache

WORKDIR /var/interlegis/sapl/

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

RUN chmod +x /var/interlegis/sapl/*.sh && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log && \
    touch /var/interlegis/sapl/sapl.log && \
    ln -s /var/interlegis/sapl/sapl.log /var/log/sapl/sapl.log

VOLUME ["/var/interlegis/sapl/data", "/var/interlegis/sapl/media"]

CMD ["/var/interlegis/sapl/start.sh"]
