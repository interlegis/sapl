FROM alpine:3.5

ENV BUILD_PACKAGES postgresql-dev graphviz-dev graphviz build-base git pkgconfig \
python3-dev libxml2-dev jpeg-dev libressl-dev libffi-dev libxslt-dev nodejs py3-lxml \
py3-magic postgresql-client vim

RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache

RUN cd /var && mkdir interlegis && cd interlegis && mkdir sapl && cd .. && cd .. &&\
    apk add --update --no-cache $BUILD_PACKAGES && \
    npm install -g bower

# Bower aceitar root
RUN touch /root/.bowerrc \
&& chmod 751 /root/.bowerrc \
&& echo "{ \"allow_root\": true }" >> /root/.bowerrc \
&& npm cache clean

WORKDIR /var/interlegis/sapl/

ADD . /var/interlegis/sapl/

COPY start.sh /var/interlegis/sapl/

RUN chmod +x /var/interlegis/sapl/start.sh

RUN pip install -r /var/interlegis/sapl/requirements/requirements.txt --upgrade setuptools

VOLUME ["/var/interlegis/sapl/data", "/var/interlegis/sapl/media", "/var/interlegis/sapl/collected_static"]
ENTRYPOINT ["/var/interlegis/sapl/start.sh"]
