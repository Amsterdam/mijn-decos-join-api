#!/bin/bash
set -e

# AZ AppService allows SSH into a App instance.
if [ $MA_OTAP_ENV == "test" ]
then
 # echo "Starting SSH ..."
service ssh start
fi

uwsgi --uid www-data --gid www-data --ini /api/uwsgi.ini