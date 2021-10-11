import os
import sentry_sdk
from flask import Flask, make_response
from openapi_core import create_spec
from openapi_core.contrib.flask.decorators import FlaskOpenAPIViewDecorator
from requests.exceptions import HTTPError
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.exceptions import HTTPException
from yaml import load
import yaml
import json

from decosjoin.api.helpers import (
    error_response_json,
    get_connection,
    get_tma_user,
    success_response_json,
    verify_tma_user,
)
from decosjoin.config import (
    BASE_PATH,
    IS_DEV,
    CustomJSONEncoder,
    TMAException,
    get_sentry_dsn,
    logger,
)
from decosjoin.crypto import decrypt

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

sentry_dsn = get_sentry_dsn()
if sentry_dsn:  # pragma: no cover
    sentry_sdk.init(
        dsn=sentry_dsn, integrations=[FlaskIntegration()], with_locals=False
    )


with open(os.path.join(BASE_PATH, "openapi.yml"), "r") as spec_file:
    spec_dict = load(spec_file, Loader=yaml.Loader)

spec = create_spec(spec_dict)

openapi = FlaskOpenAPIViewDecorator.from_spec(spec)


@app.route("/decosjoin/getvergunningen", methods=["GET"])
@openapi
@verify_tma_user
def get_vergunningen():
    user = get_tma_user()
    zaken = get_connection().get_zaken(user["type"], user["id"])
    return success_response_json(zaken)


@app.route("/decosjoin/listdocuments/<string:encrypted_zaak_id>", methods=["GET"])
@openapi
@verify_tma_user
def get_documents(encrypted_zaak_id):
    user = get_tma_user()
    zaak_id = decrypt(encrypted_zaak_id, user["id"])

    documents = get_connection().get_documents(zaak_id, user["id"])
    return success_response_json(documents)


@app.route("/decosjoin/document/<string:encrypted_doc_id>", methods=["GET"])
@openapi
@verify_tma_user
def get_document_blob(encrypted_doc_id):
    user = get_tma_user()

    doc_id = decrypt(encrypted_doc_id, user["id"])
    document = get_connection().get_document_blob(doc_id)

    new_response = make_response(document["file_data"])
    new_response.headers["Content-Type"] = document["Content-Type"]

    return new_response


@app.route("/status/health")
@openapi
def health_check():
    response = make_response(json.dumps("OK"))
    response.headers["Content-type"] = "application/json"
    return response


@app.errorhandler(Exception)
@openapi
def handle_error(error):
    print("blapperdeblap")
    error_message_original = str(error)

    msg_tma_exception = "TMA error occurred"
    msg_request_http_error = "Request error occurred"
    msg_server_error = "Server error occurred"

    if not app.config["TESTING"]:
        logger.exception(
            error, extra={"error_message_original": error_message_original}
        )

    if IS_DEV:
        msg_tma_exception = error_message_original
        msg_request_http_error = error_message_original
        msg_server_error = error_message_original

    if isinstance(error, HTTPError):
        return error_response_json(
            msg_request_http_error,
            error.response.status_code,
        )
    elif isinstance(error, TMAException):
        return error_response_json(msg_tma_exception, 400)

    return error_response_json(msg_server_error, 500)


if __name__ == "__main__":  # pragma: no cover
    app.run()
