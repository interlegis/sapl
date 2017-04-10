FROM alpine:3.5

ENV BUILD_PACKAGES postgresql-dev graphviz-dev graphviz build-base git pkgconfig \
python3-dev libxml2-dev jpeg-dev libressl-dev libffi-dev libxslt-dev nodejs py3-lxml \
py3-magic postgresql-client

RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache

RUN mkdir /sapl && apk add --update --no-cache $BUILD_PACKAGES && npm install -g bower

# Bower aceitar root
RUN touch /root/.bowerrc \
&& chmod 751 /root/.bowerrc \
&& echo "{ \"allow_root\": true }" >> /root/.bowerrc \
&& npm cache clean

WORKDIR /sapl

ADD . /sapl

RUN pip install -r requirements/dev-requirements.txt --upgrade setuptools --no-cache-dir \
&& python3 manage.py bower install
