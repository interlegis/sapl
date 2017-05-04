FROM alpine:3.5

ENV BUILD_PACKAGES postgresql-dev graphviz-dev graphviz build-base git pkgconfig \
python3-dev libxml2-dev jpeg-dev libressl-dev libffi-dev libxslt-dev nodejs py3-lxml \
py3-magic postgresql-client vim

RUN apk add --no-cache python3 nginx && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache && \
    rm -f /etc/nginx/conf.d/*

RUN mkdir -p /var/interlegis/sapl && \
    apk add --update --no-cache $BUILD_PACKAGES && \
    npm install -g bower && \
    npm cache clean

WORKDIR /var/interlegis/sapl/

ADD . /var/interlegis/sapl/

COPY start.sh /var/interlegis/sapl/
COPY config/nginx/sapl.conf /etc/nginx/conf.d
COPY config/nginx/nginx.conf /etc/nginx/nginx.conf

RUN pip install -r /var/interlegis/sapl/requirements/dev-requirements.txt --upgrade setuptools && \
    rm -r /root/.cache && \
    rm -r /tmp/*

COPY config/env_dockerfile /var/interlegis/sapl/sapl/.env

RUN python3 manage.py bower install -- --allow-root && \
    python3 manage.py collectstatic --no-input && \
    rm -rf /var/interlegis/sapl/sapl/.env && \
    rm -rf /var/interlegis/sapl/sapl.db 

RUN chmod +x /var/interlegis/sapl/start.sh && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

VOLUME ["/var/interlegis/sapl/data", "/var/interlegis/sapl/media"]

CMD ["/var/interlegis/sapl/start.sh"]
