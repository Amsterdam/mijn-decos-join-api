import os
import os.path


BASE_PATH = os.path.abspath(os.path.dirname(__file__))


def get_sentry_dsn():
    return os.getenv('SENTRY_DSN', None)


def get_decosjoin_username():
    return os.getenv("DECOS_JOIN_USERNAME")


def get_decosjoin_password():
    return os.getenv("DECOS_JOIN_PASSWORD")


def get_decosjoin_api_host():
    return os.getenv("DECOS_JOIN_API_HOST")


def get_decosjoin_adres_boeken_bsn():
    return os.getenv("DECOS_JOIN_ADRES_BOEKEN_BSN").split(',')


def get_decosjoin_adres_boeken_kvk():
    return os.getenv("DECOS_JOIN_ADRES_BOEKEN_KVK").split(',')


def get_decosjoin_adres_boeken():
    return {
        'bsn': get_decosjoin_adres_boeken_bsn(),
        'kvk': get_decosjoin_adres_boeken_kvk(),
    }


def get_key():
    return os.getenv("MIJN_DECOS_KEY")


def get_tma_certificate():
    tma_cert_location = os.getenv('TMA_CERTIFICATE')
    with open(tma_cert_location) as f:
        return f.read()
