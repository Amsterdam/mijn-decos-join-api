from pprint import pprint
from sys import argv

from app.decosjoin_connection import DecosJoinConnection
from app.config import (
    get_decosjoin_username,
    get_decosjoin_password,
    get_decosjoin_api_host,
    get_decosjoin_adres_boeken,
)
import app.decosjoin_connection
from app.crypto import decrypt

bsn = argv[1]

if argv[2] == "-d":
    zaak_id = decrypt(argv[3])
else:
    zaak_id = argv[2]


app.decosjoin_connection.LOG_RAW = True

connection = DecosJoinConnection(
    get_decosjoin_username(),
    get_decosjoin_password(),
    get_decosjoin_api_host(),
    get_decosjoin_adres_boeken(),
)

documents = connection.get_documents(zaak_id, bsn)
pprint(documents)
