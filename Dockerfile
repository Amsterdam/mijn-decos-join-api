FROM amsterdam/python:3.9.6-buster

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
