FROM amsterdam/python:3.9.6-buster

WORKDIR /api

COPY app /api/app
COPY scripts /api/scripts
COPY requirements.txt /api
COPY uwsgi.ini /api

COPY /test.sh /api
COPY .flake8 /api

RUN pip install --no-cache-dir -r /api/requirements.txt

USER datapunt
CMD uwsgi --ini /api/uwsgi.ini
