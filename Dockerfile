FROM ubuntu:15.04

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN mkdir /sapl

RUN echo "deb http://archive.ubuntu.com/ubuntu/ vivid universe" | tee -a "/etc/apt/sources.list"

RUN \
	apt-get update && \
	apt-get install -y -f \
	software-properties-common \
	libpq-dev \
	graphviz-dev \
	graphviz \
	build-essential \
	git \
	pkg-config \
	python3-dev \
	libxml2-dev \
	libjpeg-dev \
	libssl-dev \
	libffi-dev \
	libxslt1-dev \
	python3-setuptools \
	curl

# use python3 in pip
RUN easy_install3 pip lxml

# install nodejs
RUN DEBIAN_FRONTEND=noninteractive curl -sL https://deb.nodesource.com/setup_5.x | bash -
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs

# install bower
RUN npm install -g bower

# Bower aceitar root
RUN touch /root/.bowerrc
RUN chmod 751 /root/.bowerrc
RUN echo "{ \"allow_root\": true }" >> /root/.bowerrc

WORKDIR /sapl

ADD . /sapl

RUN pip install -r requirements/dev-requirements.txt
RUN pip install --upgrade setuptools

# RUN python3 manage.py bower install
