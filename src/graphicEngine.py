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

class Scene:
    def __init__(self):
        self.next = None

    def init_tf(self, x, y, w, h, text=''):
        tf = TextField(x, y, w, h, text)
        self.focusable.append(tf)
        self.triggerable.append(tf)
        self.renderable.append(tf)
        return tf

    def update(self):
        pass

class Menu(Scene):
    def __init__(self):
        super().__init__()

