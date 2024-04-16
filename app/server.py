import logging
import os

from azure.monitor.opentelemetry import configure_azure_monitor
from flask import Flask, make_response, request
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.propagate import extract
from opentelemetry.trace import SpanKind, get_tracer_provider
from requests.exceptions import HTTPError

from app import auth
from app.config import (
    IS_DEV,
    UpdatedJSONProvider,
    get_application_insights_connection_string,
)
from app.crypto import decrypt
from app.helpers import error_response_json, get_connection, success_response_json

logger_name = __name__
logger = logging.getLogger(logger_name)

# See also: https://medium.com/@tedisaacs/auto-instrumenting-python-fastapi-and-monitoring-with-azure-application-insights-768a59d2f4b9
if get_application_insights_connection_string():
    configure_azure_monitor()

tracer = trace.get_tracer(__name__, tracer_provider=get_tracer_provider())

app = Flask(__name__)
app.json = UpdatedJSONProvider(app)

FlaskInstrumentor.instrument_app(app)


@app.route("/decosjoin/getvergunningen", methods=["GET"])
@auth.login_required
def get_vergunningen():
    with tracer.start_as_current_span("/getvergunningen"):
        user = auth.get_current_user()
        zaken = get_connection().get_zaken(user["type"], user["id"])

        return success_response_json(zaken)


@app.route("/decosjoin/listdocuments/<string:encrypted_zaak_id>", methods=["GET"])
@auth.login_required
def get_documents(encrypted_zaak_id):
    with tracer.start_as_current_span("/listdocuments"):
        user = auth.get_current_user()
        zaak_id = decrypt(encrypted_zaak_id, user["id"])
        documents = get_connection().get_documents(zaak_id, user["id"])

        return success_response_json(documents)


@app.route("/decosjoin/document/<string:encrypted_doc_id>", methods=["GET"])
@auth.login_required
def get_document_blob(encrypted_doc_id):
    with tracer.start_as_current_span("/document"):
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

    return error_response_json(
        msg_server_error, error.code if hasattr(error, "code") else 500
    )


if __name__ == "__main__":  # pragma: no cover
    app.run()
