from pprint import pprint
from sys import argv
from app.auth import PROFILE_TYPE_COMMERCIAL

from app.decosjoin_service import DecosJoinConnection
from app.config import (
    get_decosjoin_username,
    get_decosjoin_password,
    get_decosjoin_api_host,
)
import app.decosjoin_service

kvk = argv[1]

connection = DecosJoinConnection(
    get_decosjoin_username(),
    get_decosjoin_password(),
    get_decosjoin_api_host(),
)

zaken = connection.get_zaken(PROFILE_TYPE_COMMERCIAL, kvk)
pprint(zaken)
