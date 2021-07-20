import logging

import sentry_sdk
from flask import Flask, make_response
from sentry_sdk.integrations.flask import FlaskIntegration

from werkzeug.exceptions import HTTPException

from decosjoin.api.helpers import (
    error_response_json,
    get_connection,
    get_tma_user,
    success_response_json,
    verify_tma_user,
)
from decosjoin.config import CustomJSONEncoder, TMAException, get_sentry_dsn
from decosjoin.crypto import decrypt

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

if get_sentry_dsn():  # pragma: no cover
    sentry_sdk.init(
        dsn=get_sentry_dsn(), integrations=[FlaskIntegration()], with_locals=False
    )


@app.route("/decosjoin/getvergunningen", methods=["GET"])
@verify_tma_user
def get_vergunningen():
    user = get_tma_user()
    zaken = get_connection().get_zaken(user["type"], user["id"])

    return success_response_json(zaken)


@app.route("/decosjoin/listdocuments/<string:encrypted_zaak_id>", methods=["GET"])
@verify_tma_user
def get_documents(encrypted_zaak_id):
    user = get_tma_user()
    zaak_id = decrypt(encrypted_zaak_id, user["id"])

    documents = get_connection().get_documents(zaak_id, user["id"])
    return success_response_json(documents)


@app.route("/decosjoin/document/<string:encrypted_doc_id>", methods=["GET"])
@verify_tma_user
def get_document_blob(encrypted_doc_id):
    user = get_tma_user()

    doc_id = decrypt(encrypted_doc_id, user["id"])
    document = get_connection().get_document_blob(doc_id)

    new_response = make_response(document["file_data"])
    new_response.headers["Content-Type"] = document["Content-Type"]

    return new_response


@app.route("/status/health")
def health_check():
    return "OK"


@app.errorhandler(Exception)
def handle_error(error):
    if isinstance(error, HTTPException):
        return error_response_json(error.description, error.code)
    elif isinstance(error, TMAException):
        return error_response_json(str(error), 400)

    return error_response_json("A server error occurred")


if __name__ == "__main__":  # pragma: no cover
    app.run()
