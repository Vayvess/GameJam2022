import json
from const import *


def rcv_tcp_msg(sock):
    try:
        data = sock.recv(MTU)
        return json.loads(data.decode("utf-8"))
    except ValueError:
        return None


def send_tcp_msg(sock, data):
    sock.sendall(json.dumps(data).encode("utf-8"))
