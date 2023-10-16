from flask import g
from flask.helpers import make_response

from app.config import (
    get_decosjoin_api_host,
    get_decosjoin_password,
    get_decosjoin_username,
)
from app.decosjoin_service import DecosJoinConnection


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
        )
    return decosjoin_service


def success_response_json(response_content):
    return make_response({"status": "OK", "content": response_content}, 200)


def error_response_json(message: str, code: int = 500):
    return make_response({"status": "ERROR", "message": message}, code)
