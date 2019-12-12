
import sentry_sdk
from flask import Flask, request
from sentry_sdk.integrations.flask import FlaskIntegration
from tma_saml import get_digi_d_bsn, InvalidBSNException

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.config import get_sentry_dsn, get_decosjoin_username, get_decosjoin_password, get_decosjoin_api_host, \
    get_decosjoin_adres_boek, get_tma_certificate

app = Flask(__name__)

if get_sentry_dsn():  # pragma: no cover
    sentry_sdk.init(
        dsn=get_sentry_dsn(),
        integrations=[FlaskIntegration()],
        with_locals=False
    )


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
        get_decosjoin_username(), get_decosjoin_password(), get_decosjoin_api_host(), get_decosjoin_adres_boek())
    try:
        bsn = get_bsn_from_request(request)
    except InvalidBSNException as e:
        return "Invalid BSN", 400
    except Exception as e:
        return str(e), 400

    zaken = connection.get_zaken(bsn)
    return {
        'status': 'OK',
        'zaken': zaken,
    }


@app.route('/status/health')
def health_check():
    return 'OK'


if __name__ == '__main__':  # pragma: no cover
    app.run()
