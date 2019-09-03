import os


def get_sentry_dsn():
    return os.getenv('SENTRY_DSN', None)


def get_decosjoin_username():
    return os.getenv("DECOS_JOIN_USERNAME")


def get_decosjoin_password():
    return os.getenv("DECOS_JOIN_PASSWORD")


def get_decosjoin_api_host():
    return os.getenv("DECOS_JOIN_API_HOST")


def get_decosjoin_adres_boek():
    return os.getenv("DECOS_JOIN_ADRES_BOEK")
