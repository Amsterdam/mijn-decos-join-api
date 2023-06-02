FROM python:latest as base

WORKDIR /api

RUN apt-get update
RUN apt-get -y install locales
RUN sed -i -e 's/# nl_NL.UTF-8 UTF-8/nl_NL.UTF-8 UTF-8/' /etc/locale.gen && \
  locale-gen
ENV LANG nl_NL.UTF-8
ENV LANGUAGE nl_NL:nl
ENV LC_ALL nl_NL.UTF-8

COPY requirements.txt /api

RUN pip install --upgrade pip \
  && pip install uwsgi \
  && pip install -r requirements.txt

COPY ./scripts /api/scripts
COPY ./app /api/app

COPY uwsgi.ini /api

COPY ./test.sh /api/
COPY .flake8 /api/

RUN chmod u+x /api/test.sh

USER datapunt
CMD uwsgi --ini /api/uwsgi.ini
