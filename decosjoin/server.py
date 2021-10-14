from werkzeug.exceptions import NotFound
import sentry_sdk
from flask import Flask, make_response
from sentry_sdk.integrations.flask import FlaskIntegration
import json

from decosjoin.api.helpers import (
    error_response_json,
    get_connection,
    get_tma_user,
    success_response_json,
    validate_openapi,
    verify_tma_user,
)
from decosjoin.config import (
    CustomJSONEncoder,
    TMAException,
    get_sentry_dsn,
    logger,
)
from decosjoin.crypto import decrypt

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

sentry_dsn = get_sentry_dsn()
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn, integrations=[FlaskIntegration()], with_locals=False
    )


@app.route("/decosjoin/getvergunningen", methods=["GET"])
@verify_tma_user
@validate_openapi
def get_vergunningen():
    user = get_tma_user()
    zaken = get_connection().get_zaken(user["type"], user["id"])
    return success_response_json(zaken)


@app.route("/decosjoin/listdocuments/<string:encrypted_zaak_id>", methods=["GET"])
@verify_tma_user
@validate_openapi
def get_documents(encrypted_zaak_id):
    user = get_tma_user()
    zaak_id = decrypt(encrypted_zaak_id, user["id"])

    documents = get_connection().get_documents(zaak_id, user["id"])
    return success_response_json(documents)


@app.route("/decosjoin/document/<string:encrypted_doc_id>", methods=["GET"])
@verify_tma_user
@validate_openapi
def get_document_blob(encrypted_doc_id):
    user = get_tma_user()

    doc_id = decrypt(encrypted_doc_id, user["id"])
    document = get_connection().get_document_blob(doc_id)

    new_response = make_response(document["file_data"])
    new_response.headers["Content-Type"] = document["Content-Type"]

    return new_response


@app.route("/status/health")
@validate_openapi
def health_check():
    response = make_response(json.dumps("OK"))
    response.headers["Content-type"] = "application/json"
    return response


@app.errorhandler(Exception)
def handle_error(error):
    msg_tma_exception = "TMA error occurred"
    msg_request_http_error = "Request error occurred"
    msg_server_error = "Server error occurred"
    msg_404_error = "Not found"

    logger.exception(error)

    if isinstance(error, NotFound):
        return error_response_json(msg_404_error, 404)
    elif isinstance(error, HTTPError):
        return error_response_json(
            msg_request_http_error,
            error.response.status_code,
        )
    elif isinstance(error, TMAException):
        return error_response_json(msg_tma_exception, 400)

    return error_response_json(msg_server_error, 500)


if __name__ == "__main__":  # pragma: no cover
    app.run()
