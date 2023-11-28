from pprint import pprint
from sys import argv

from app.decosjoin_service import DecosJoinConnection
from app.config import (
    get_decosjoin_username,
    get_decosjoin_password,
    get_decosjoin_api_host,
)
import app.decosjoin_service

zaak_id = argv[1]
step_title = argv[2]

connection = DecosJoinConnection(
    get_decosjoin_username(),
    get_decosjoin_password(),
    get_decosjoin_api_host(),
)

workflow_date = connection.get_workflow_date_by_step_title(zaak_id, step_title)
pprint(workflow_date)
