import logging
from datetime import date, time

import sentry_sdk
from cryptography.fernet import InvalidToken
from flask import Flask, request, make_response
from flask.json import JSONEncoder
from sentry_sdk.integrations.flask import FlaskIntegration
from tma_saml import get_digi_d_bsn, SamlVerificationException, get_e_herkenning_attribs, \
    HR_KVK_NUMBER_KEY

import tma_saml

from decosjoin.api.decosjoin.Exception import MissingSamlTokenException, InvalidBSNException, SamlException, \
    GeneralError
from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.config import get_sentry_dsn, get_decosjoin_username, get_decosjoin_password, get_decosjoin_api_host, \
    get_decosjoin_adres_boeken, get_tma_certificate
from decosjoin.crypto import decrypt

logger = logging.getLogger(__name__)
app = Flask(__name__)

if get_sentry_dsn():  # pragma: no cover
    sentry_sdk.init(
        dsn=get_sentry_dsn(),
        integrations=[FlaskIntegration()],
        with_locals=False
    )


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, time):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()

        return JSONEncoder.default(self, obj)


app.json_encoder = CustomJSONEncoder


def get_bsn_from_request(request):
    """
    Get the BSN based on a request, expecting a SAML token in the headers
    """
    # Load the TMA certificate
    tma_certificate = get_tma_certificate()

    # Decode the BSN from the request with the TMA certificate
    bsn = get_digi_d_bsn(request, tma_certificate)
    return bsn


def get_kvk_number_from_request(request):
    """
    Get the KVK number from the request headers.
    """
    # Load the TMA certificate
    tma_certificate = get_tma_certificate()

    # Decode the BSN from the request with the TMA certificate
    attribs = get_e_herkenning_attribs(request, tma_certificate)
    kvk = attribs[HR_KVK_NUMBER_KEY]
    return kvk


def _get_kind_and_identifier_or_error(request):
    kind = None
    identifier = None

    try:
        identifier = get_kvk_number_from_request(request)
        kind = 'kvk'
    except SamlVerificationException:
        raise MissingSamlTokenException
    except KeyError:
        # does not contain kvk number, might still contain BSN
        pass

    if not identifier:
        try:
            identifier = get_bsn_from_request(request)
            kind = 'bsn'
        except tma_saml.InvalidBSNException:
            raise InvalidBSNException
        except SamlVerificationException as e:
            raise SamlException(e.args[0])
        except Exception as e:
            logger.error("Error", type(e), str(e))
            raise GeneralError

    return kind, identifier


@app.route('/decosjoin/getvergunningen', methods=['GET'])
def get_vergunningen():
    try:
        kind, identifier = _get_kind_and_identifier_or_error(request)
    except (MissingSamlTokenException, InvalidBSNException, SamlException, GeneralError) as e:
        return e.message, e.status_code

    connection = DecosJoinConnection(get_decosjoin_username(), get_decosjoin_password(), get_decosjoin_api_host(), get_decosjoin_adres_boeken())
    zaken = connection.get_zaken(kind, identifier)
    return {
        'status': 'OK',
        'content': zaken,
    }


@app.route('/decosjoin/listdocuments/<string:encrypted_zaak_id>', methods=['GET'])
def list_documents(encrypted_zaak_id):
    connection = DecosJoinConnection(
        get_decosjoin_username(), get_decosjoin_password(), get_decosjoin_api_host(), get_decosjoin_adres_boeken())

    try:
        kind, identifier = _get_kind_and_identifier_or_error(request)
    except (MissingSamlTokenException, InvalidBSNException, SamlException, GeneralError) as e:
        return e.message, e.status_code

    try:
        zaak_id = decrypt(encrypted_zaak_id, identifier)
    except InvalidToken:
        return {'status': "ERROR", "message": "decryption zaak ID invalid"}, 400
    documents = connection.list_documents(zaak_id, identifier)
    return {
        'status': 'OK',
        'content': documents
    }


@app.route('/decosjoin/document/<string:encrypted_doc_id>', methods=['GET'])
def get_document(encrypted_doc_id):
    connection = DecosJoinConnection(
        get_decosjoin_username(), get_decosjoin_password(), get_decosjoin_api_host(), get_decosjoin_adres_boeken())

    try:
        kind, identifier = _get_kind_and_identifier_or_error(request)
    except (MissingSamlTokenException, InvalidBSNException, SamlException, GeneralError) as e:
        return e.message, e.status_code

    try:
        doc_id = decrypt(encrypted_doc_id, identifier)
        document = connection.get_document(doc_id)
    except InvalidToken:
        return {"status": "ERROR", "message": "decryption zaak ID invalid"}, 400
    except Exception as e:
        logger.error("Error", type(e), str(e))
        return {"status": "ERROR", "message": "Unknown Error"}, 400

    new_response = make_response(document['file_data'])
    new_response.headers["Content-Type"] = document["Content-Type"]
    return new_response


@app.route('/status/health')
def health_check():
    return 'OK'


if __name__ == '__main__':  # pragma: no cover
    app.run()
