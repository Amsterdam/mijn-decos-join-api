import json
import os.path

from decosjoin.config import BASE_PATH


FIXTURE_PATH = os.path.join(BASE_PATH, 'tests', 'fixtures')


def _load_fixture(json_file_name):
    with open(os.path.join(FIXTURE_PATH, json_file_name)) as fh:
        return json.load(fh)


def get_search_addresses_bsn_111222333_response_empty():
    return _load_fixture('search_addresses_bsn_111222333_empty.json')


def get_search_addresses_bsn_111222333_response():
    return _load_fixture('search_addresses_bsn_111222333.json')


def get_search_addresses_bsn_111222333_response_2():
    return _load_fixture('search_addresses_bsn_111222333_2.json')


def get_zaken_response():
    return _load_fixture('zaken_response.json')


def get_zaken_response_2():
    return _load_fixture('zaken_response2.json')


def get_zaken_resposne_2_part_2():
    return _load_fixture('zaken_response2_part2.json')


def get_zaken_response_empty():
    return _load_fixture('zaken_response_empty.json')


def get_documents_response():
    return _load_fixture('documents_response.json')


def get_blob_response():
    return _load_fixture("blob_response.json")


def get_blob_response_no_pdf():
    return _load_fixture("blob_response_no_pdf.json")


def get_blobs_response():
    return _load_fixture('blobs_response.json')


def get_document_response():
    return _load_fixture('document_response.json')


def get_document2_response():
    return _load_fixture('document2_response.json')


def get_document():
    with open(os.path.join(FIXTURE_PATH, 'test.pdf'), 'rb') as fh:
        return fh.read()
