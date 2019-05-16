FROM alpine:3.8

ENV BUILD_PACKAGES postgresql-dev graphviz-dev graphviz build-base git pkgconfig \
                   python3-dev libxml2-dev jpeg-dev libressl-dev libffi-dev libxslt-dev \
                   nodejs py3-lxml py3-magic postgresql-client poppler-utils antiword \
                   curl jq openssh-client vim bash

RUN apk update --update-cache && apk upgrade

RUN apk --update add fontconfig ttf-dejavu && fc-cache -fv

RUN apk add --no-cache python3 nginx tzdata && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache && \
    rm -f /etc/nginx/conf.d/*

RUN mkdir -p /var/interlegis/sapl && \
    apk add --update --no-cache $BUILD_PACKAGES

ADD . /var/interlegis/sapl/

WORKDIR /var/interlegis/sapl/

RUN pip install -r /var/interlegis/sapl/requirements/dev-requirements.txt --upgrade setuptools && \
    rm -r /root/.cache

COPY docker_devel/.env /var/interlegis/sapl/sapl/.env

RUN python3 manage.py collectstatic --noinput --clear

# Remove .env(fake) e sapl.db da imagem
RUN rm -rf /var/interlegis/sapl/sapl/.env && \
    rm -rf /var/interlegis/sapl/sapl.db

RUN chmod +x /var/interlegis/sapl/start.sh && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log && \
    mkdir /var/log/sapl/ && touch /var/interlegis/sapl/sapl.log && \
    ln -s /var/interlegis/sapl/sapl.log /var/log/sapl/sapl.log

VOLUME [ "/var/interlegis/sapl"]

EXPOSE 8000

CMD python3 manage.py runserver 0.0.0.0:8000

#CMD ["/var/interlegis/sapl/start.sh"]
