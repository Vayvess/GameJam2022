import os
import csv
import time
import socket
import selectors
import threading
from random import randint
from const import *


colls = []
with open(os.path.join("../ressources/arena.csv")) as f:
    fbuff = csv.reader(f, delimiter=',')
    for row in fbuff:
        colls.append([tile != "0" for tile in row])

clk = pg.time.Clock()
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.bind(SRV_ADDR)
tcp_sock.listen()
gameobjects = []
lock = threading.Lock()

tcp_sock.setblocking(False)
sel = selectors.DefaultSelector()
sel.register(tcp_sock, selectors.EVENT_READ, None)
game_id = 0


class Lava:
    def __init__(self, x, y, d):
        global game_id
        self.id = game_id
        game_id += 1

        self.timer = 750
        self.type = UDP_LAVA
        if d == TCP_DOWN:
            self.pos = (x - 96, y + 96)
        elif d == TCP_UP:
            self.pos = (x - 96, y - 256)
        elif d == TCP_RIGHT:
            self.pos = (x + 64, y - 96)
        elif d == TCP_LEFT:
            self.pos = (x - 256, y - 96)

    def get_state(self):
        return {
            UDP_TYPE: UDP_LAVA,
            UDP_POS: self.pos
        }

    def update(self, dt):
        self.timer -= dt
        if self.timer < 0:
            gameobjects.remove(self)


class Bot:
    def __init__(self):
        global game_id
        self.id = game_id
        game_id += 1
        self.type = UDP_BOT

        self.lp = 100
        self.x = 400
        self.y = 300
        self.d = 0

    def reset(self):
        self.lp = 100
        self.x = 400
        self.y = 300

    def get_state(self):
        return {
            UDP_TYPE: UDP_BOT,
            UDP_POS: (self.x, self.y)
        }

    def update(self, dt):
        for go in gameobjects:
            if go.type == UDP_LAVA:
                if pg.rect.Rect(go.pos[0], go.pos[1], 192, 192).collidepoint(self.x, self.y):
                    self.lp -= 1
                    if self.lp == 0:
                        self.reset()

        if randint(0, 99) < 5:
            self.d = randint(0, 3)
        if self.d == 0:
            tmp_x = self.x + 0.2 * dt
            if colls[int((self.y + 332) // 64)][int((tmp_x + 432) // 64)]:
                self.x = tmp_x
        elif self.d == 1:
            tmp_x = self.x - 0.2 * dt
            if colls[int((self.y + 332)) // 64][int((tmp_x + 432) // 64)]:
                self.x = tmp_x
        elif self.d == 2:
            tmp_y = self.y + 0.2 * dt
            if colls[int((tmp_y + 332) // 64)][int((self.x + 432) // 64)]:
                self.y = tmp_y
        elif self.d == 3:
            tmp_y = self.y - 0.2 * dt
            if colls[int((tmp_y + 332) // 64)][int((self.x + 432) // 64)]:
                self.y = tmp_y


class Session:
    def __init__(self, conn, addr):
        global game_id
        self.id = game_id
        game_id += 1

        self.type = UDP_PLAYER
        self.conn = conn
        self.addr = addr
        self.inputs = {
            TCP_UP: False,
            TCP_DOWN: False,
            TCP_LEFT: False,
            TCP_RIGHT: False,
            TCP_LAVA: False
        }

        self.lp = 100
        self.mp = 100
        self.dir = TCP_DOWN
        self.x = 400
        self.y = 300
        self.usern = "anon"

    def handle_play_req(self, req):
        send_tcp_msg(self.conn, self.id)
        self.usern = req[TCP_USERN]
        gameobjects.append(self)

    def handle_req(self, req):
        req_type = req[TCP_REQ]
        if req_type == TCP_PLAY:
            self.handle_play_req(req)
        elif req_type == TCP_INPUT:
            self.inputs = req

    def reset(self):
        self.lp = 100
        self.mp = 100
        self.x = 400
        self.y = 300

    def get_state(self):
        return {
            UDP_TYPE: UDP_PLAYER,
            UDP_POS: (self.x, self.y),
            UDP_USERN: self.usern,
            UDP_MANA: int(self.mp),
            UDP_LP: self.lp,
            UDP_DIR: self.dir
        }

    def update(self, dt):
        for go in gameobjects:
            if go.type == UDP_LAVA:
                if pg.rect.Rect(go.pos[0], go.pos[1], 192, 192).collidepoint(self.x, self.y):
                    self.lp -= 1
                    if self.lp == 0:
                        self.reset()

        if self.inputs[TCP_RIGHT]:
            tmp_x = self.x + 0.2 * dt
            if colls[int((self.y + 300) // 64)][int((tmp_x + 400) // 64)]:
                self.x = tmp_x
            self.dir = TCP_RIGHT
        if self.inputs[TCP_LEFT]:
            tmp_x = self.x - 0.2 * dt
            if colls[int((self.y + 300) // 64)][int((tmp_x + 400) // 64)]:
                self.x = tmp_x
            self.dir = TCP_LEFT
        if self.inputs[TCP_UP]:
            tmp_y = self.y - 0.2 * dt
            if colls[int((tmp_y + 300) // 64)][int((self.x + 400) // 64)]:
                self.y = tmp_y
            self.dir = TCP_UP
        if self.inputs[TCP_DOWN]:
            tmp_y = self.y + 0.2 * dt
            if colls[int((tmp_y + 300) // 64)][int((self.x + 400) // 64)]:
                self.y = tmp_y
            self.dir = TCP_DOWN

        if self.inputs[TCP_LAVA]:
            self.inputs[TCP_LAVA] = False
            if self.mp > 50:
                gameobjects.append(Lava(self.x, self.y, self.dir))
                self.mp -= 50
        if self.mp < 100:
            self.mp += 0.4


def gameloop():
    weights = {
        UDP_PLAYER: 75,
        UDP_LAVA: 25,
        UDP_BOT: 25
    }

    def broadcast_state(gs):
        data = json.dumps(gs).encode("utf-8")
        if len(data) > MTU:
            return
        for obj in gameobjects:
            if obj.type == UDP_PLAYER:
                udp_sock.sendto(data, obj.addr)

    gameobjects.append(Bot())
    gameobjects.append(Bot())
    gameobjects.append(Bot())
    gameobjects.append(Bot())
    gameobjects.append(Bot())
    while True:
        if gameobjects:
            dt = clk.tick(60)
            lock.acquire()
            w = 0
            game_state = {}
            for go in gameobjects:
                go.update(dt)
                if w + weights[go.type] > MTU:
                    broadcast_state(game_state)
                    game_state = {}
                    w = 0
                game_state[go.id] = go.get_state()
                w += weights[go.type]
            broadcast_state(game_state)
            lock.release()
        else:
            time.sleep(2)


def tcp_handler():
    try:
        while True:
            evs = sel.select(None)
            for key, mask in evs:
                if key.data is None:
                    conn, addr = tcp_sock.accept()
                    conn.setblocking(False)
                    sel.register(conn, selectors.EVENT_READ, Session(conn, addr))
                    print("anon joined the server !")
                else:
                    sess = key.data
                    data = sess.conn.recv(MTU)
                    if data:
                        try:
                            sess.handle_req(json.loads(data.decode("utf-8")))
                        except json.decoder.JSONDecodeError:
                            pass
                    else:
                        print(f"{sess.usern} disconnected !")
                        lock.acquire()
                        if sess in gameobjects:
                            gameobjects.remove(sess)
                        lock.release()
                        sel.unregister(sess.conn)
                        sess.conn.close()
    except KeyboardInterrupt:
        print("Server down !")


threading.Thread(target=gameloop, daemon=True).start()
tcp_handler()
sel.close()
tcp_sock.close()
