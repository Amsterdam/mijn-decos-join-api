import json
import os.path

from decosjoin.config import BASE_PATH


FIXTURE_PATH = os.path.join(BASE_PATH, 'tests', 'fixtures')


def _load_fixture(json_file_name):
    with open(os.path.join(FIXTURE_PATH, json_file_name)) as fh:
        return json.load(fh)


def get_bsn_lookup_response():
    return _load_fixture('bsn_lookup.json')


def get_GPP_zaken_response():
    return _load_fixture('gpp_case.json')


def get_GGP_casetype_response():
    return _load_fixture('gpp_casetype.json')


def get_GPK_casetype_response():
    return _load_fixture('gpk_casetype.json')
