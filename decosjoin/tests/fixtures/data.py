import json
import os.path

from decosjoin.config import BASE_PATH


def _load_fixture(json_file_name):
    with open(os.path.join(BASE_PATH, json_file_name)) as fh:
        return json.load(fh)


def get_bsn_lookup_response():
    return _load_fixture('bsn_lookup.json')


def get_GPP_zaken_response():
    return _load_fixture('gpp_case.json')
