
import sentry_sdk
from flask import Flask
from sentry_sdk.integrations.flask import FlaskIntegration

from decosjoin.config import get_sentry_dsn

app = Flask(__name__)


if get_sentry_dsn():  # pragma: no cover
    sentry_sdk.init(
        dsn=get_sentry_dsn(),
        integrations=[FlaskIntegration()],
        with_locals=False
    )


@app.route('/decosjoin/getvergunningen', methods=['GET'])
def get_vergunningen():
    return {
        'status': 'OK',
        'data': [],
    }


@app.route('/status/health')
def health_check():
    return 'OK'


if __name__ == '__main__':  # pragma: no cover
    app.run()
