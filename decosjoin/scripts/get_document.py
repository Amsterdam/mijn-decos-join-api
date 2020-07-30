from pprint import pprint
from sys import argv

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.config import get_decosjoin_username, get_decosjoin_password, get_decosjoin_api_host, \
    get_decosjoin_adres_boeken
import decosjoin.api.decosjoin.decosjoin_connection
from decosjoin.crypto import decrypt

if argv[1] == "-d":
    document_id = decrypt(argv[2])
else:
    document_id = argv[1]


decosjoin.api.decosjoin.decosjoin_connection.log_raw = True

connection = DecosJoinConnection(
    get_decosjoin_username(), get_decosjoin_password(), get_decosjoin_api_host(), get_decosjoin_adres_boeken())

document = connection.get_document(document_id)
# printing is done by log_raw
