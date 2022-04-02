import json
from const import *

data = {
    UDP_TYPE: UDP_PLAYER,
    UDP_POS: (500, 325),
    "2": "Barghest"
}

print(len(json.dumps(data).encode("utf-8")))