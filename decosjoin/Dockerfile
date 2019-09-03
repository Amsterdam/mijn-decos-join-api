FROM amsterdam/python

MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y
RUN pip install --upgrade pip
RUN pip install uwsgi

COPY /api /decosjoin/api
COPY /requirements.txt /decosjoin

COPY test.sh /decosjoin
COPY .flake8 /decosjoin/

RUN pip install --no-cache-dir -r /decosjoin/requirements.txt

#ENTRYPOINT ["uwsgi"]
USER datapunt
CMD uwsgi
