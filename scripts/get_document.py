from sys import argv

from app.decosjoin_service import DecosJoinConnection
from app.config import (
    get_decosjoin_username,
    get_decosjoin_password,
    get_decosjoin_api_host,
)
import app.decosjoin_service
from app.crypto import decrypt

if argv[1] == "-d":
    document_id = decrypt(argv[2])
else:
    document_id = argv[1]


app.decosjoin_service.LOG_RAW = True

connection = DecosJoinConnection(
    get_decosjoin_username(),
    get_decosjoin_password(),
    get_decosjoin_api_host(),
)

document = connection.get_document_blob(document_id)
# printing is done by LOG_RAW
