#!/bin/bash
set -e

uwsgi --uid www-data --gid www-data --ini /api/uwsgi.ini