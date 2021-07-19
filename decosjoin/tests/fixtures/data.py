import json
import os.path

from decosjoin.config import BASE_PATH


FIXTURE_PATH = os.path.join(BASE_PATH, 'tests', 'fixtures')


def load_fixture(json_file_name):
    with open(os.path.join(FIXTURE_PATH, json_file_name)) as fh:
        return json.load(fh)


def get_search_addresses_bsn_111222333_response_empty():
    return load_fixture('search_addresses_bsn_111222333_empty.json')


def get_search_addresses_bsn_111222333_response():
    return load_fixture('search_addresses_bsn_111222333.json')


def get_search_addresses_bsn_111222333_response_2():
    return load_fixture('search_addresses_bsn_111222333_2.json')


def get_zaken_response():
    return load_fixture('zaken_response.json')


def get_zaken_response_2():
    return load_fixture('zaken_response2.json')


def get_zaken_response_2_part_2():
    return load_fixture('zaken_response2_part2.json')


def get_zaken_response_2_part_3():
    return load_fixture('zaken_response2_part3.json')


def get_zaken_response_empty():
    return load_fixture('zaken_response_empty.json')


def get_documents_response():
    return load_fixture('documents_response.json')


def get_blob_response():
    return load_fixture("blob_response.json")


def get_blob_response_no_pdf():
    return load_fixture("blob_response_no_pdf.json")


def get_blobs_response():
    return load_fixture('blobs_response.json')


def get_document_response():
    return load_fixture('document_response.json')


def get_document2_response():
    return load_fixture('document2_response.json')


def get_document():
    with open(os.path.join(FIXTURE_PATH, 'test.pdf'), 'rb') as fh:
        return fh.read()
