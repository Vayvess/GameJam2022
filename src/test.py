import sys
import time
import pygame as pg
from const import *

pg.init()
clock = pg.time.Clock()
pg.display.set_caption("Louvain-li-Nux 2022")
window = pg.display.set_mode(DIM)

fps = 60
dt = 1 / fps

x = 0
while True:
    for ev in pg.event.get():
        if ev.type == pg.QUIT:
            pg.quit()
            sys.exit()
        if ev.type == pg.KEYDOWN or ev.type == pg.KEYUP:
            new_input = True

    if new_input:
        x += 1
        inputs = pg.key.get_pressed()
        data = {
            TCP_REQ: TCP_INPUT,
            TCP_UP: inputs[pg.K_z],
            TCP_DOWN: inputs[pg.K_s],
            TCP_LEFT: inputs[pg.K_q],
            TCP_RIGHT: inputs[pg.K_d],
        }
        new_input = False

    dt = clock.tick(fps)
    window.fill(BLACK)
    pg.display.flip()
