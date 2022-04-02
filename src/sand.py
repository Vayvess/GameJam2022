import json
from const import *

data = 5
u = json.dumps(data).encode("utf-8")
v = json.loads(u.decode("utf-8"))
print(type(v))
