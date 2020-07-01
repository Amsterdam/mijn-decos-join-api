import json
import os.path

from decosjoin.config import BASE_PATH


FIXTURE_PATH = os.path.join(BASE_PATH, 'tests', 'fixtures')


def _load_fixture(json_file_name):
    with open(os.path.join(FIXTURE_PATH, json_file_name)) as fh:
        return json.load(fh)


def get_addresses_bsn_111222333_response_empty():
    return _load_fixture('addresses_bsn_111222333_empty.json')


def get_addresses_bsn_111222333_response():
    return _load_fixture('addresses_bsn_111222333.json')


def get_addresses_bsn_111222333_response_2():
    return _load_fixture('addresses_bsn_111222333_2.json')


def get_zaken_response():
    return _load_fixture('zaken_response.json')


def get_zaken_response_2():
    return _load_fixture('zaken_response2.json')


def get_zaken_response_empty():
    return _load_fixture('zaken_response_empty.json')
