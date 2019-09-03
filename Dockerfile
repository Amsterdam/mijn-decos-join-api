FROM amsterdam/python

MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y
RUN pip install --upgrade pip
RUN pip install uwsgi

WORKDIR /app

COPY /requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY test.sh /app/
COPY .flake8 /app/

COPY decosjoin /app/decosjoin

#ENTRYPOINT ["uwsgi"]
USER datapunt
CMD uwsgi
