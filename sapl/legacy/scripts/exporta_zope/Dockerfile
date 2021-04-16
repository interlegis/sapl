FROM python:2.7.18-buster
RUN apt-get update && apt-get install -y git-annex
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
