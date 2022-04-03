import json
from const import *

import socket

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setblocking(False)
udp_sock.bind(("localhost", 60002))

while True:
    try:
        print(udp_sock.recv(1024))
    except socket.error as err:
        print(err)
