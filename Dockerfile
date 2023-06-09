FROM python:latest as base

ENV PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=off \
  REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /api

COPY ca/* /usr/local/share/ca-certificates/extras/

RUN apt-get update \
  && apt-get dist-upgrade -y \
  && apt-get autoremove -y \
  && apt-get install --no-install-recommends -y \
  nano \
  locales \
  && rm -rf /var/lib/apt/lists/* /var/cache/debconf/*-old \
  && pip install --upgrade pip \
  && pip install uwsgi \
  && chmod -R 644 /usr/local/share/ca-certificates/extras/ \
  && update-ca-certificates

RUN sed -i -e 's/# nl_NL.UTF-8 UTF-8/nl_NL.UTF-8 UTF-8/' /etc/locale.gen && \
  locale-gen
ENV LANG nl_NL.UTF-8
ENV LANGUAGE nl_NL:nl
ENV LC_ALL nl_NL.UTF-8

COPY requirements.txt /api

RUN pip install -r requirements.txt

COPY ./scripts /api/scripts
COPY ./app /api/app
COPY ./uwsgi.ini /api
COPY ./test.sh /api
COPY .flake8 /api

RUN chmod u+x /api/test.sh

CMD uwsgi --uid www-data --gid www-data --ini /api/uwsgi.ini
