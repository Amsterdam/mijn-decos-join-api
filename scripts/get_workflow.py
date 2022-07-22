from pprint import pprint
from sys import argv

from app.decosjoin_service import DecosJoinConnection
from app.config import (
    get_decosjoin_username,
    get_decosjoin_password,
    get_decosjoin_api_host,
    get_decosjoin_adres_boeken,
)
import app.decosjoin_service

zaak_id = argv[1]

app.decosjoin_service.LOG_RAW = True

connection = DecosJoinConnection(
    get_decosjoin_username(),
    get_decosjoin_password(),
    get_decosjoin_api_host(),
    get_decosjoin_adres_boeken(),
)

workflow = connection.get_workflow(zaak_id)
pprint(workflow)
