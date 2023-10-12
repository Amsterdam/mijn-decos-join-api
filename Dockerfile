FROM python:3.11-bookworm as base

ENV TZ=Europe/Amsterdam
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=off
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /api

COPY ca/* /usr/local/share/ca-certificates/extras/

RUN apt-get update \
  && apt-get dist-upgrade -y \
  && apt-get autoremove -y \
  && apt-get install -y --no-install-recommends nano openssh-server locales \
  && pip install --upgrade pip \
  && pip install uwsgi \
  && chmod -R 644 /usr/local/share/ca-certificates/extras/ \
  && update-ca-certificates

RUN sed -i -e 's/# nl_NL.UTF-8 UTF-8/nl_NL.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG nl_NL.UTF-8
ENV LANGUAGE nl_NL:nl
ENV LC_ALL nl_NL.UTF-8

COPY requirements.txt /api

RUN pip install -r requirements.txt

COPY ./scripts /api/scripts
COPY ./app /api/app

FROM base as tests

COPY conf/test.sh /api/
COPY .flake8 /api/

RUN chmod u+x /api/test.sh

ENTRYPOINT [ "/bin/sh", "/api/test.sh"]

FROM base as publish

# ssh ( see also: https://github.com/Azure-Samples/docker-django-webapp-linux )
ENV SSH_PASSWD "root:Docker!"

EXPOSE 8000
ENV PORT 8000

ARG MA_OTAP_ENV
ENV MA_OTAP_ENV=$MA_OTAP_ENV

ARG MA_BUILD_ID
ENV MA_BUILD_ID=$MA_BUILD_ID

ARG MA_GIT_SHA
ENV MA_GIT_SHA=$MA_GIT_SHA

COPY conf/uwsgi.ini /api/
COPY conf/docker-entrypoint.sh /api/
COPY conf/sshd_config /etc/ssh/

RUN chmod u+x /api/docker-entrypoint.sh \
  && echo "$SSH_PASSWD" | chpasswd

ENTRYPOINT [ "/bin/sh", "/api/docker-entrypoint.sh"]

FROM publish as publish-final

COPY /files /app/files
