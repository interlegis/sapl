FROM debian:9.6-slim

ENV BUILD_PACKAGES apt-file apt-utils libpq-dev graphviz-dev graphviz build-essential git pkg-config \
                   python3-dev libxml2-dev libjpeg-dev libssl-dev libffi-dev libxslt-dev \
                   nodejs nodejs python3-lxml python3-magic postgresql-client poppler-utils antiword \
                   curl jq openssh-client vim openssh-client bash

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y fontconfig ttf-dejavu && fc-cache -fv

RUN apt-get install -y python3 python3-pip nginx tzdata && \
    pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache && \
    rm -f /etc/nginx/conf.d/*

RUN mkdir -p /var/interlegis/sapl && \
    apt-get install -y $BUILD_PACKAGES && \
    npm install -g bower && \
    npm cache verify

WORKDIR /var/interlegis/sapl/

ADD . /var/interlegis/sapl/

COPY start.sh /var/interlegis/sapl/
COPY config/nginx/sapl.conf /etc/nginx/conf.d
COPY config/nginx/nginx.conf /etc/nginx/nginx.conf

RUN pip install -r /var/interlegis/sapl/requirements/dev-requirements.txt --upgrade setuptools && \
    rm -r /root/.cache

COPY config/env_dockerfile /var/interlegis/sapl/sapl/.env

# Configura timezone para BRT
# RUN cp /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && echo "America/Sao_Paulo" > /etc/timezone

# manage.py bower install bug: https://github.com/nvbn/django-bower/issues/51

# compilescss - Precompile all occurrences of your SASS/SCSS files for the whole project into css files

RUN python3 manage.py bower_install --allow-root && \
    python3 manage.py compilescss

RUN python3 manage.py collectstatic --noinput --clear

# Remove .env(fake) e sapl.db da imagem
RUN rm -rf /var/interlegis/sapl/sapl/.env && \
    rm -rf /var/interlegis/sapl/sapl.db

RUN chmod +x /var/interlegis/sapl/start.sh && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log && \
    mkdir /var/log/sapl/

VOLUME ["/var/interlegis/sapl/data", "/var/interlegis/sapl/media"]

CMD ["/var/interlegis/sapl/start.sh"]
