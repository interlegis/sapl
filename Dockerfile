FROM debian:jessie-slim
#FROM python:3.7-slim

ENV BUILD_PACKAGES apt-file libpq-dev graphviz-dev graphviz build-essential git pkg-config \
                   python3-dev libxml2-dev libjpeg-dev libssl-dev libffi-dev libxslt1-dev pgadmin3 \
                   python3-lxml python3-magic postgresql-contrib postgresql-client \
                   python3-psycopg2 poppler-utils antiword curl jq vim openssh-client bash \
                   software-properties-common python3-setuptools python3-venv nginx tzdata nodejs 


ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends apt-utils

# GENERATING LOCALES
# RUN apt-get update && apt-get install -y locales
# RUN locale-gen en_US en_US.UTF-8 && locale-gen pt_BR pt_BR.UTF-8 && dpkg-reconfigure locales
#  && update-locale LANG=pt_BR.UTF-8
# ENV LANG pt_BR.UTF-8
# RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
#  && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
# ENV LANG en_US.utf8

RUN mkdir -p /usr/share/man/man1 && \
    mkdir -p /usr/share/man/man7 && apt-get upgrade -y && \
    apt-get install apt-utils -y && apt-get install -y software-properties-common
RUN apt-get install -y fontconfig ttf-dejavu && fc-cache -fv


RUN apt-get install -y python python3-pip && \
    pip3 install --upgrade pip setuptools && \
    rm -f /etc/nginx/conf.d/*

#RUN add-apt-repository ppa:deadsnakes/ppa -y


RUN mkdir -p /var/interlegis/sapl && \
    apt-get install -y $BUILD_PACKAGES

#RUN curl -sL https://deb.nodesource.com/setup_8.x | bash - && apt-get install -y nodejs

WORKDIR /var/interlegis/sapl/

ADD . /var/interlegis/sapl/

COPY start.sh /var/interlegis/sapl/
COPY config/nginx/sapl.conf /etc/nginx/conf.d
COPY config/nginx/nginx.conf /etc/nginx/nginx.conf

RUN pip install -r /var/interlegis/sapl/requirements/dev-requirements.txt --upgrade setuptools && \
    rm -r /root/.cache

COPY config/env_dockerfile /var/interlegis/sapl/sapl/.env

RUN python3 manage.py collectstatic --noinput --clear

# Remove .env(fake) e sapl.db da imagem
RUN rm -rf /var/interlegis/sapl/sapl/.env && \
    rm -rf /var/interlegis/sapl/sapl.db

RUN chmod +x /var/interlegis/sapl/start.sh && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log && \
    mkdir /var/log/sapl/

# Debian não possui usuário 'nginx' necessário para o Debian
RUN useradd --no-create-home nginx

ENV DEBIAN_FRONTEND teletype

EXPOSE 80/tcp 443/tcp

VOLUME ["/var/interlegis/sapl/data", "/var/interlegis/sapl/media"]

CMD ["/var/interlegis/sapl/start.sh"]
