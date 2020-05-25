FROM amsterdam/python:3.8-buster

MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y
RUN pip install --upgrade pip
RUN pip install uwsgi

WORKDIR /app

COPY /requirements.txt /app/
COPY uwsgi.ini /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY test.sh /app/
COPY .flake8 /app/

COPY decosjoin /app/decosjoin

USER datapunt
CMD uwsgi --ini /app/uwsgi.ini
