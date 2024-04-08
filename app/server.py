import logging
import os

import sentry_sdk
from flask import Flask, make_response
from requests.exceptions import HTTPError
from sentry_sdk.integrations.flask import FlaskIntegration

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

from app import auth
from app.config import IS_AZ, IS_DEV, SENTRY_ENV, UpdatedJSONProvider, get_sentry_dsn
from app.crypto import decrypt
from app.helpers import (
    error_response_json,
    get_connection,
    success_response_json,
)
# configure_azure_monitor(
   # connection_string=os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING"))

app = Flask(__name__)
app.json = UpdatedJSONProvider(app)

sentry_dsn = get_sentry_dsn()
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=f"{'az-' if IS_AZ else ''}{SENTRY_ENV}",
        integrations=[FlaskIntegration()],
        with_locals=False,
    )


@app.route("/decosjoin/getvergunningen", methods=["GET"])
@auth.login_required
def get_vergunningen():
    user = auth.get_current_user()
    zaken = get_connection().get_zaken(user["type"], user["id"])

    return success_response_json(zaken)


@app.route("/decosjoin/listdocuments/<string:encrypted_zaak_id>", methods=["GET"])
@auth.login_required
def get_documents(encrypted_zaak_id):
    user = auth.get_current_user()
    zaak_id = decrypt(encrypted_zaak_id, user["id"])
    documents = get_connection().get_documents(zaak_id, user["id"])

    return success_response_json(documents)


@app.route("/decosjoin/document/<string:encrypted_doc_id>", methods=["GET"])
@auth.login_required
def get_document_blob(encrypted_doc_id):
    user = auth.get_current_user()

    doc_id = decrypt(encrypted_doc_id, user["id"])
    document = get_connection().get_document_blob(doc_id)

    new_response = make_response(document["file_data"])
    new_response.headers["Content-Type"] = document["Content-Type"]

    return new_response


@app.route("/")
@app.route("/status/health")
def health_check():
    return success_response_json(
        {
            "gitSha": os.getenv("MA_GIT_SHA", -1),
            "buildId": os.getenv("MA_BUILD_ID", -1),
            "otapEnv": os.getenv("MA_OTAP_ENV", None),
        }
    )


@app.errorhandler(Exception)
def handle_error(error):
    error_message_original = f"{type(error)}:{str(error)}"

    msg_auth_exception = "Auth error occurred"
    msg_request_http_error = "Request error occurred"
    msg_server_error = "Server error occurred"

    logging.exception(error, extra={"error_message_original": error_message_original})

    if IS_DEV:  # pragma: no cover
        msg_auth_exception = error_message_original
        msg_request_http_error = error_message_original
        msg_server_error = error_message_original

    if isinstance(error, HTTPError):
        return error_response_json(
            msg_request_http_error,
            error.response.status_code,
        )
    elif auth.is_auth_exception(error):
        return error_response_json(msg_auth_exception, 401)

    return error_response_json(msg_server_error, 500)


if __name__ == "__main__":  # pragma: no cover
    print(os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING"))
    app.run()
