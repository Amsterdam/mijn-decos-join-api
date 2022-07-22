import os
from functools import wraps

import yaml
from flask import g, request
from flask.helpers import make_response
from openapi_core import create_spec
from openapi_core.contrib.flask import FlaskOpenAPIRequest, FlaskOpenAPIResponse
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.validation.response.validators import ResponseValidator
from yaml import load

from app.config import (
    BASE_PATH,
    ENABLE_OPENAPI_VALIDATION,
    get_decosjoin_adres_boeken,
    get_decosjoin_api_host,
    get_decosjoin_password,
    get_decosjoin_username,
)
from app.decosjoin_service import DecosJoinConnection

openapi_spec = None


def get_openapi_spec():
    global openapi_spec
    if not openapi_spec:
        with open(os.path.join(BASE_PATH, "openapi.yml"), "r") as spec_file:
            spec_dict = load(spec_file, Loader=yaml.Loader)
        openapi_spec = create_spec(spec_dict)

    return openapi_spec


def validate_openapi(function):
    @wraps(function)
    def validate(*args, **kwargs):

        if ENABLE_OPENAPI_VALIDATION:
            spec = get_openapi_spec()
            openapi_request = FlaskOpenAPIRequest(request)
            validator = RequestValidator(spec)
            result = validator.validate(openapi_request)
            result.raise_for_errors()

        response = function(*args, **kwargs)

        if ENABLE_OPENAPI_VALIDATION:
            openapi_response = FlaskOpenAPIResponse(response)
            validator = ResponseValidator(spec)
            result = validator.validate(openapi_request, openapi_response)
            result.raise_for_errors()

        return response

    return validate


def get_connection():
    """Creates a DecosJoin connection instance if there is none yet for the
    current application context.
    """
    decosjoin_service = g.get("decosjoin_service", None)
    if not decosjoin_service:
        decosjoin_service = g.decosjoin_service = DecosJoinConnection(
            get_decosjoin_username(),
            get_decosjoin_password(),
            get_decosjoin_api_host(),
            get_decosjoin_adres_boeken(),
        )
    return decosjoin_service


def success_response_json(response_content):
    return make_response({"status": "OK", "content": response_content}, 200)


def error_response_json(message: str, code: int = 500):
    return make_response({"status": "ERROR", "message": message}, code)
