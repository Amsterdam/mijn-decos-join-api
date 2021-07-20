class DecosJoinConnectionError(Exception):
    pass


class ParseError(Exception):
    pass


class MissingSamlTokenException(Exception):
    message = {"status": "ERROR", "message": "Missing SAML token"}
    status_code = 400


class InvalidBSNException(Exception):
    message = {"status": "ERROR", "message": "Invalid BSN"}
    status_code = 400


class SamlException(Exception):
    status_code = 400

    def __init__(self, message, errors):
        message = {"status": "ERROR", "message": message}
        super().__init__(message)


class GeneralError(Exception):
    status_code = 400
    message = {"status": "ERROR", "message": "Unknown Error"}
