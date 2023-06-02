FROM python:latest as base

WORKDIR /api

RUN apt-get update
RUN apt-get -y install locales
RUN sed -i -e 's/# nl_NL.UTF-8 UTF-8/nl_NL.UTF-8 UTF-8/' /etc/locale.gen && \
  locale-gen
ENV LANG nl_NL.UTF-8
ENV LANGUAGE nl_NL:nl
ENV LC_ALL nl_NL.UTF-8

ENV PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=off \
  REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY ca/* /usr/local/share/ca-certificates/extras/

RUN chmod -R 644 /usr/local/share/ca-certificates/extras/ \
  && update-ca-certificates

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

COPY docker-entrypoint.sh /api/
RUN chmod u+x /api/docker-entrypoint.sh

ENTRYPOINT [ "/bin/sh", "/api/docker-entrypoint.sh"]
