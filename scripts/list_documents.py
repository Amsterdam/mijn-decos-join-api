from pprint import pprint
from sys import argv

from app.decosjoin_service import DecosJoinConnection
from app.config import (
    get_decosjoin_username,
    get_decosjoin_password,
    get_decosjoin_api_host,
)
import app.decosjoin_service
from app.crypto import decrypt

bsn = argv[1]

if argv[2] == "-d":
    zaak_id = decrypt(argv[3])
else:
    zaak_id = argv[2]


connection = DecosJoinConnection(
    get_decosjoin_username(),
    get_decosjoin_password(),
    get_decosjoin_api_host(),
)

documents = connection.get_documents(zaak_id, bsn)
pprint(documents)
