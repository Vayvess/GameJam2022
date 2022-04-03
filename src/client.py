import sys
import time
import socket
import threading
from const import *

game_id = 0
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    tcp_sock.connect(SRV_ADDR)
except ConnectionRefusedError as err:
    print(err)
    sys.exit()
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind(tcp_sock.getsockname())


def req_srv(req, call_back):
    send_tcp_msg(tcp_sock, req)
    res = rcv_tcp_msg(tcp_sock)
    if res is None:
        pg.quit()
        tcp_sock.close()
        sys.exit()
    call_back(res)


pg.init()
clock = pg.time.Clock()
font = pg.font.Font(None, 32)
pg.display.set_caption("Louvain-li-Nux 2022")
window = pg.display.set_mode(DIM)
bg = pg.image.load("../ressources/arena.png").convert()
spell_lava = pg.image.load("../ressources/spell_lava.png").convert()
bot = pg.image.load("../ressources/bot.png")


class Text:
    def __init__(self, x, y, text, color):
        self.color = color
        self.text = text
        self.origin = pg.Vector2(x, y)
        self.text_pos = pg.Vector2(x - len(text) * 2, y)
        self.text_surf = font.render(text, True, color)

    def set_color(self, color):
        self.color = color
        self.text_surf = font.render(self.text, True, color)

    def set_text(self, text):
        self.text = text
        self.text_pos.x = self.origin.x - len(text) * 2
        self.text_surf = font.render(text, True, self.color)

    def reset(self, text, color):
        self.text = text
        self.color = color
        self.text_pos.x = self.origin.x - len(text) * 2
        self.text_surf = font.render(text, True, color)

    def render(self, win):
        win.blit(self.text_surf, self.text_pos)


class TextField:
    def __init__(self, x, y, w, h, text):
        self.rect = pg.Rect(x, y, w, h)
        self.color = GREY
        self.active = False

        self.text = text
        self.text_pos = pg.Vector2(
            x - len(text) * 6 + w // 2,
            y - 8 + h // 2
        )
        self.text_surf = font.render(text, True, self.color)

    def focus(self, event):
        if self.rect.collidepoint(event.pos):
            self.active = True
            self.color = BLUE
        else:
            self.active = False
            self.color = GREY

    def trigger(self, event):
        if self.active:
            if event.key == pg.K_BACKSPACE:
                if len(self.text):
                    self.text_pos.x += 6
                    self.text = self.text[:-1]
            elif event.unicode.isalnum():
                self.text_pos.x -= 6
                self.text += event.unicode
            self.text_surf = font.render(self.text, True, self.color)

    def render(self, win):
        win.blit(self.text_surf, self.text_pos)
        pg.draw.rect(win, self.color, self.rect, 2)


class Button:
    def __init__(self, x, y, w, h, f, text):
        self.rect = pg.Rect(x, y, w, h)
        self.color = GREY
        self.f = f

        self.text = text
        self.text_pos = pg.Vector2(
            x - len(text) * 6 + w // 2,
            y - 8 + h // 2
        )
        self.text_surf = font.render(text, True, self.color)

    def focus(self, event):
        if self.rect.collidepoint(event.pos):
            self.f()

    def render(self, win):
        win.blit(self.text_surf, self.text_pos)
        pg.draw.rect(win, self.color, self.rect, 2)


class Scene:
    def __init__(self):
        self.next = None
        self.focusable = []
        self.triggerable = []
        self.renderable = []

    def handle_focus(self, event):
        for f in self.focusable:
            f.focus(event)

    def handle_trigger(self, event):
        for t in self.triggerable:
            t.trigger(event)

    def handle_render(self):
        window.fill(BLACK)
        for r in self.renderable:
            r.render(window)

    def init_tf(self, x, y, w, h, text=''):
        tf = TextField(x, y, w, h, text)
        self.focusable.append(tf)
        self.triggerable.append(tf)
        self.renderable.append(tf)
        return tf

    def show_btn(self, btn):
        self.focusable.append(btn)
        self.renderable.append(btn)

    def mask_btn(self, btn):
        self.focusable.remove(btn)
        self.renderable.remove(btn)

    def show_txt(self, txt):
        self.renderable.append(txt)

    def mask_txt(self, txt):
        self.renderable.remove(txt)

    def update(self):
        clock.tick(60)
        for ev in pg.event.get():
            if ev.type == pg.KEYDOWN:
                self.handle_trigger(ev)
            elif ev.type == pg.MOUSEBUTTONDOWN:
                self.handle_focus(ev)
            elif ev.type == pg.QUIT:
                tcp_sock.close()
                pg.quit()
                sys.exit()
        self.handle_render()
        pg.display.flip()


class Arena(Scene):
    def __init__(self):
        super().__init__()
        self.uptimes = {}
        self.gameobjects = {}
        self.lock = threading.Lock()
        self.pos = (400, 300)

        def sub_routine():
            try:
                while 1:
                    data = json.loads(udp_sock.recv(MTU).decode("utf-8"))
                    now = time.time()
                    self.lock.acquire()
                    for k in data:
                        self.uptimes[k] = now
                        self.gameobjects[k] = data[k]
                    to_remove = []
                    for k in self.uptimes:
                        if now - self.uptimes[k] > 0.75:
                            to_remove.append(k)
                    for k in to_remove:
                        self.uptimes.pop(k)
                        self.gameobjects.pop(k)
                    self.lock.release()
            except OSError:
                pass
        threading.Thread(target=sub_routine, daemon=True).start()

    def handle_render(self):
        window.fill(BLACK)
        window.blit(bg, (-self.pos[0], -self.pos[1]))
        # TODO: ANIMATE REMOTE OBJ
        self.lock.acquire()
        for k, v in self.gameobjects.items():
            if v[UDP_TYPE] == UDP_PLAYER:
                if int(k) == game_id:
                    self.pos = v[UDP_POS]
                    pg.draw.circle(window, BLUE, (400, 300), 16)
                    if v[UDP_DIR] == TCP_DOWN:
                        pg.draw.line(window, WHITE, (400, 300), (400, 316), 4)
                    elif v[UDP_DIR] == TCP_UP:
                        pg.draw.line(window, WHITE, (400, 300), (400, 284), 4)
                    elif v[UDP_DIR] == TCP_LEFT:
                        pg.draw.line(window, WHITE, (400, 300), (384, 300), 4)
                    elif v[UDP_DIR] == TCP_RIGHT:
                        pg.draw.line(window, WHITE, (400, 300), (416, 300), 4)

                    window.blit(font.render(v[UDP_USERN], True, WHITE), (400 - len(v[UDP_USERN]) * 6, 260))
                    pg.draw.rect(window, BLUE, (750, 0, 25, v[UDP_MANA] * 6))
                    pg.draw.rect(window, GREEN, (775, 0, 25, v[UDP_LP] * 6))
                else:
                    pos = v[UDP_POS]
                    pos = (pos[0] - self.pos[0] + 400, pos[1] - self.pos[1] + 300)
                    pg.draw.circle(window, RED, pos, 16)
                    pos = (pos[0] - len(v[UDP_USERN]) * 6, pos[1] - 40)
                    window.blit(font.render(v[UDP_USERN], True, WHITE), pos)
            elif v[UDP_TYPE] == UDP_LAVA:
                pos = v[UDP_POS]
                pos = (pos[0] - self.pos[0] + 400, pos[1] - self.pos[1] + 300)
                window.blit(spell_lava, pos)
            elif v[UDP_TYPE] == UDP_BOT:
                pos = v[UDP_POS]
                pos = (pos[0] - self.pos[0] + 400, pos[1] - self.pos[1] + 300)
                window.blit(bot, pos)

        self.lock.release()

        for r in self.renderable:
            r.render(window)
        pg.display.flip()

    def update(self):
        clock.tick(60)
        to_send = False
        for ev in pg.event.get():
            if ev.type == pg.KEYDOWN or ev.type == pg.KEYUP:
                to_send = True
            elif ev.type == pg.QUIT:
                tcp_sock.close()
                udp_sock.close()
                pg.quit()
                sys.exit()
        if to_send:
            inputs = pg.key.get_pressed()
            send_tcp_msg(tcp_sock, {
                TCP_REQ: TCP_INPUT,
                TCP_UP: inputs[pg.K_z],
                TCP_DOWN: inputs[pg.K_s],
                TCP_LEFT: inputs[pg.K_q],
                TCP_RIGHT: inputs[pg.K_d],
                TCP_LAVA: inputs[pg.K_e]
            })
        self.handle_render()


class Menu(Scene):
    def __init__(self):
        super().__init__()
        usern_tf = self.init_tf(300, 250, 200, 50)

        def req_play():
            def ans_play(ans):
                global game_id
                game_id = ans
                self.next = Arena()

            req_srv({
                TCP_REQ: TCP_PLAY,
                TCP_USERN: usern_tf.text
            }, ans_play)

        play_btn = Button(300, 325, 200, 50, req_play, "Play")
        self.show_btn(play_btn)


dt = 1 / FPS
curr_scene = Menu()
while True:
    if curr_scene.next is not None:
        curr_scene = curr_scene.next
    curr_scene.update()
