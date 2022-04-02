import socket
import selectors
from const import *

tcp_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
tcp_sock.bind(SRV_ADDR)
tcp_sock.listen()

tcp_sock.setblocking(False)
sel = selectors.DefaultSelector()
sel.register(tcp_sock, selectors.EVENT_READ, None)

try:
    while True:
        evs = sel.select(None)
        for key, mask in evs:
            if key.data is None:
                conn, addr = tcp_sock.accept()
                conn.setblocking(False)
                sel.register(conn, selectors.EVENT_READ, 'hello')
                print("new connection")
            else:
                # TODO: handle req
                conn = key.fileobj
                data = conn.recv(MTU)
                if data:
                    data = json.loads(data.decode("utf-8"))
                    print(data)
                else:
                    print("bye")
                    sel.unregister(conn)
                    conn.close()
except KeyboardInterrupt:
    print("Server down !")

sel.close()
tcp_sock.close()
