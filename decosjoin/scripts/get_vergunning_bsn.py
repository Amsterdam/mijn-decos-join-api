from pprint import pprint
from sys import argv

from tma_saml.user_type import UserType

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.config import (
    get_decosjoin_username,
    get_decosjoin_password,
    get_decosjoin_api_host,
    get_decosjoin_adres_boeken,
)
import decosjoin.api.decosjoin.decosjoin_connection

bsn = argv[1]

decosjoin.api.decosjoin.decosjoin_connection.LOG_RAW = True

connection = DecosJoinConnection(
    get_decosjoin_username(),
    get_decosjoin_password(),
    get_decosjoin_api_host(),
    get_decosjoin_adres_boeken(),
)

zaken = connection.get_zaken(UserType.BURGER, bsn)
pprint(zaken)
