import time
import socket
import selectors
import threading

from const import *
from proto import *

tcp_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
tcp_sock.bind(SRV_ADDR)
tcp_sock.listen()
gameobjects = []

tcp_sock.setblocking(False)
sel = selectors.DefaultSelector()
sel.register(tcp_sock, selectors.EVENT_READ, None)


class Session:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr



        self.lp = 100
        self.mp = 100
        self.x = 400
        self.y = 300
        self.usern = "anon"

    def handle_play_req(self, req):
        send_tcp_msg(self.conn, True)
        self.usern = req[TCP_USERN]
        gameobjects.append(self)

    def handle_req(self, req):
        req_type = req[TCP_REQ]
        if req_type == TCP_PLAY:
            self.handle_play_req(req)

    def reset(self):
        self.lp = 100
        self.mp = 100
        self.x = 400
        self.y = 300

    def update(self):
        pass


def gameloop():
    while True:
        if gameobjects:
            for go in gameobjects:
                go.update()
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
                else:
                    sess = key.data
                    data = sess.conn.recv(MTU)
                    if data:
                        sess.handle_req(json.loads(data.decode("utf-8")))
                    else:
                        if sess in gameobjects:
                            gameobjects.remove(sess)
                        sel.unregister(sess.conn)
                        sess.conn.close()
    except KeyboardInterrupt:
        print("Server down !")


threading.Thread(target=gameloop(), daemon=True).start()
tcp_handler()
sel.close()
tcp_sock.close()
