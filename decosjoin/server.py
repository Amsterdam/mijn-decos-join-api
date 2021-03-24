import logging
from datetime import date, time

import sentry_sdk
from cryptography.fernet import InvalidToken
from flask import Flask, request, make_response
from flask.json import JSONEncoder
from sentry_sdk.integrations.flask import FlaskIntegration
from tma_saml import get_digi_d_bsn, InvalidBSNException, SamlVerificationException, get_e_herkenning_attribs, \
    HR_KVK_NUMBER_KEY

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


@app.route('/decosjoin/getvergunningen', methods=['GET'])
def get_vergunningen():
    kind = None
    identifier = None

    try:
        identifier = get_kvk_number_from_request(request)
        kind = 'kvk'
    except SamlVerificationException:
        return {'status': 'ERROR', 'message': 'Missing SAML token'}, 400
    except KeyError:
        # does not contain kvk number, might still contain BSN
        pass

    if not identifier:
        try:
            identifier = get_bsn_from_request(request)
            kind = 'bsn'
        except InvalidBSNException:
            return {"status": "ERROR", "message": "Invalid BSN"}, 400
        except SamlVerificationException as e:
            return {"status": "ERROR", "message": e.args[0]}, 400
        except Exception as e:
            logger.error("Error", type(e), str(e))
            return {"status": "ERROR", "message": "Unknown Error"}, 400

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
        bsn = get_bsn_from_request(request)
    except InvalidBSNException:
        return {"status": "ERROR", "message": "Invalid BSN"}, 400
    except SamlVerificationException as e:
        return {"status": "ERROR", "message": e.args[0]}, 400
    except Exception as e:
        logger.error("Error", type(e), str(e))
        return {"status": "ERROR", "message": "Unknown Error"}, 400

    try:
        zaak_id = decrypt(encrypted_zaak_id, bsn)
    except InvalidToken:
        return {'status': "ERROR", "message": "decryption zaak ID invalid"}, 400
    documents = connection.list_documents(zaak_id, bsn)
    return {
        'status': 'OK',
        'content': documents
    }


@app.route('/decosjoin/document/<string:encrypted_doc_id>', methods=['GET'])
def get_document(encrypted_doc_id):
    connection = DecosJoinConnection(
        get_decosjoin_username(), get_decosjoin_password(), get_decosjoin_api_host(), get_decosjoin_adres_boeken())
    try:
        bsn = get_bsn_from_request(request)
        doc_id = decrypt(encrypted_doc_id, bsn)
        document = connection.get_document(doc_id)
    except InvalidBSNException:
        return {"status": "ERROR", "message": "Invalid BSN"}, 400
    except SamlVerificationException as e:
        return {"status": "ERROR", "message": e.args[0]}, 400
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
