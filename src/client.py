import sys
import socket
import pygame as pg
from const import *

tcp_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
try:
    tcp_sock.connect(SRV_ADDR)
except ConnectionRefusedError as err:
    print(err)
    sys.exit()

pg.init()
clock = pg.time.Clock()
pg.display.set_caption("Louvain-li-Nux 2022")
screen = pg.display.set_mode(DIM)

dt = 1 / FPS
while True:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            tcp_sock.close()
            sys.exit()
    screen.fill(BLACK)
    pg.display.update()
    dt = clock.tick(FPS)
