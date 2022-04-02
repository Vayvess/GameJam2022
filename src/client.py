import sys
import socket
import pygame as pg
from const import *
from proto import *

tcp_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
try:
    tcp_sock.connect(SRV_ADDR)
except ConnectionRefusedError as err:
    print(err)
    sys.exit()
udp_sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
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

    def update(self):
        clock.tick(60)
        for ev in pg.event.get():
            pass


class Menu(Scene):
    def __init__(self):
        super().__init__()
        usern_tf = self.init_tf(300, 250, 200, 50)

        def req_play():
            def ans_play(ans):
                if ans:
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
