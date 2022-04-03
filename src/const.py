import json
import pygame as pg


def rcv_tcp_msg(sock):
    try:
        data = sock.recv(MTU)
        return json.loads(data.decode("utf-8"))
    except ValueError:
        return None


def send_tcp_msg(sock, data):
    sock.sendall(json.dumps(data).encode("utf-8"))


pg.init()
FPS = 60
MTU = 1300
DIM = (W, H) = 800, 600
SRV_PORT = 65002
SRV_IP = "localhost"
SRV_ADDR = (SRV_IP, SRV_PORT)

# COLORS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREY = (125, 125, 125)

# TCP REQ TYPE
TCP_REQ = "0"
TCP_PLAY = "1"
TCP_INPUT = "2"

# TCP PLAY
TCP_USERN = "1"

# TCP INPUT
TCP_UP = "1"
TCP_DOWN = "2"
TCP_LEFT = "3"
TCP_RIGHT = "4"

# UDP FIELDS
UDP_TYPE = "0"
UDP_POS = "1"
UDP_USERN = "2"

# UDP TYPES
UDP_PLAYER = "0"
