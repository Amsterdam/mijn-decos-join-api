import logging
from datetime import date, time

import sentry_sdk
from flask import Flask, request
from flask.json import JSONEncoder
from sentry_sdk.integrations.flask import FlaskIntegration
from tma_saml import get_digi_d_bsn, InvalidBSNException, SamlVerificationException

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


@app.route('/decosjoin/getvergunningen', methods=['GET'])
def get_vergunningen():
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

    zaken = connection.get_zaken(bsn)
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

    zaak_id = decrypt(encrypted_zaak_id)
    documents = connection.list_documents(zaak_id)
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
    except InvalidBSNException:
        return {"status": "ERROR", "message": "Invalid BSN"}, 400
    except SamlVerificationException as e:
        return {"status": "ERROR", "message": e.args[0]}, 400
    except Exception as e:
        logger.error("Error", type(e), str(e))
        return {"status": "ERROR", "message": "Unknown Error"}, 400

    doc_id = decrypt(encrypted_doc_id)
    document = connection.get_document(doc_id)
    return {
        'status': 'OK',
        'content': document
    }


@app.route('/status/health')
def health_check():
    return 'OK'


if __name__ == '__main__':  # pragma: no cover
    app.run()
