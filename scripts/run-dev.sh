#!/usr/bin/env bash

export DECOS_JOIN_ADRES_BOEKEN_BSN="foo,bar"
export DECOS_JOIN_ADRES_BOEKEN_KVK="bar,foo"
export FLASK_ENV=development
export FLASK_APP=./app/server.py:app

flask run
