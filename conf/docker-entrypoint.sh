#!/bin/bash
set -e

# echo "Starting SSH ..."
service ssh start

uwsgi --uid www-data --gid www-data --ini /api/uwsgi.ini