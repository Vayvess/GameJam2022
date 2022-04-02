import time
import socket
import selectors
import threading
import pygame as pg
from proto import *

pg.init()
clk = pg.time.Clock()
udp_sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
tcp_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
tcp_sock.bind(SRV_ADDR)
tcp_sock.listen()
gameobjects = []
lock = threading.Lock()

tcp_sock.setblocking(False)
sel = selectors.DefaultSelector()
sel.register(tcp_sock, selectors.EVENT_READ, None)
game_id = 0


class Session:
    def __init__(self, conn, addr):
        global game_id
        self.id = game_id
        self.type = UDP_PLAYER
        game_id += 1
        self.conn = conn
        self.addr = addr
        self.inputs = {
            TCP_UP: False,
            TCP_DOWN: False,
            TCP_LEFT: False,
            TCP_RIGHT: False,
        }

        self.lp = 100
        self.mp = 100
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
            UDP_USERN: self.usern
        }

    def update(self, dt):
        if self.inputs[TCP_RIGHT]:
            self.x = self.x + 0.2 * dt
        if self.inputs[TCP_LEFT]:
            self.x = self.x - 0.2 * dt
        if self.inputs[TCP_UP]:
            self.y = self.y - 0.2 * dt
        if self.inputs[TCP_DOWN]:
            self.y = self.y + 0.2 * dt


def gameloop():
    weights = {
        UDP_PLAYER: 60
    }

    def broadcast_state(gs):
        data = json.dumps(gs).encode("utf-8")
        if len(data) > MTU:
            print("wtf")
        for obj in gameobjects:
            if obj.type == UDP_PLAYER:
                udp_sock.sendto(data, obj.addr)

    while True:
        if gameobjects:
            lock.acquire()
            dt = clk.tick(60)
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
                    print("new connection")
                else:
                    sess = key.data
                    data = sess.conn.recv(MTU)
                    if data:
                        sess.handle_req(json.loads(data.decode("utf-8")))
                    else:
                        print("bye !")
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
