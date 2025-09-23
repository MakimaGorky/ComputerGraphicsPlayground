
import pygame as pg
import numpy as np


class Button:
    def __init__(self, rect, text, callback, font=None, color=(100,100,200), hover=(150,150,250)):
        self.rect = pg.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover = hover
        self.font = font or pg.font.SysFont(None, 28)
        self.is_hover = False

    def draw(self):
        pg.draw.rect(screen, self.hover if self.is_hover else self.color, self.rect, border_radius=8)
        text_surf = self.font.render(self.text, True, (255,255,255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def update(self, event):
        if event.type == pg.MOUSEMOTION:
            self.is_hover = self.rect.collidepoint(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN and self.is_hover:
            self.callback()



def terminate():
    pg.quit()
    sys.exit()


def rgb2hsv(rgb):
    r, g, b = rgb[...,0], rgb[...,1], rgb[...,2]

    maxc = np.max(rgb, axis=-1)
    minc = np.min(rgb, axis=-1)
    Δc = (maxc - minc)

    h = np.zeros_like(maxc)
    s = Δc / maxc
    v = maxc

    rmask = (maxc == r)
    gmask = (maxc == g)
    bmask = (maxc == b)

    rc = (maxc - r) / Δc
    gc = (maxc - g) / Δc
    bc = (maxc - b) / Δc

    h[rmask] = bc[rmask] - gc[rmask]
    h[gmask] = rc[gmask] - bc[gmask] + 2
    h[bmask] = gc[bmask] - rc[bmask] + 4
    h = (h / 6.0) % 1.0

    return np.stack([h, s, v], axis=-1)


def hsv2rgb(hsv):
    h, s, v = hsv[...,0], hsv[...,1], hsv[...,2]
    i = np.floor(h * 6).astype(int)  # номер сектора
    f = h * 6 - i  # дробная часть сектора
    p = v * (1 - s)  # минимальное значение канала
    q = v * (1 - f * s)  # промежуточное значение
    t = v * (1 - (1 - f) * s)  # промежуточное значение, но в другую сторону

    rgb = np.zeros_like(hsv)

    rgb[...,0] = np.choose(i % 6, [v, q, p, p, t, v])
    rgb[...,1] = np.choose(i % 6, [t, v, v, q, p, p])
    rgb[...,2] = np.choose(i % 6, [p, p, t, v, v, q])
    return rgb


class HsvServiceVariation:
    def __init__(self, image_path):
        self.image = pg.image.load(image_path).convert()
        self.rgb = pg.surfarray.array3d(self.image).astype(np.float32) / 255.0
        self.hsv = rgb2hsv(self.rgb)
        self.h_shift = 0.0
        self.s_shift = 0.0
        self.v_shift = 0.0

        self.position = (10, 10)
        self.h_slider = Slider('H', 0, 1, 650, 300)
        self.s_slider = Slider('S', -0.5, 0.5, 650, 350)
        self.v_slider = Slider('V', -0.5, 0.5, 650, 400)

        self.surf = pg.surfarray.make_surface(np.transpose(self.rgb, (1,0,2)).swapaxes(0,1))


    def draw(self):
        x, y = self.position

        hsv = self.hsv.copy()
        hsv[...,0] = (hsv[...,0] + self.h_shift) % 1.0
        hsv[...,1] = np.clip(hsv[...,1] + self.s_shift, 0, 1)
        hsv[...,2] = np.clip(hsv[...,2] + self.v_shift, 0, 1)
        rgb = (hsv2rgb(hsv) * 255).astype(np.uint8)
        self.surf = pg.surfarray.make_surface(np.transpose(rgb, (1,0,2)).swapaxes(0,1))

        screen.blit(self.surf, (x, y))

        self.h_slider.draw()
        self.s_slider.draw()
        self.v_slider.draw()

    def update(self, event):
        self.h_slider.update(event)
        self.s_slider.update(event)
        self.v_slider.update(event)

        self.h_shift = self.h_slider.value
        self.s_shift = self.s_slider.value
        self.v_shift = self.v_slider.value

    def export(self):
        pg.image.save(self.surf, "output.png")


class Slider:
    def __init__(self, label, min_value, max_value, x, y):
        self.label = label
        self.value = 0.0
        self.min_value = min_value
        self.max_value = max_value

        self.pos = (x, y)
        self.dragging = False

    def draw(self):
        x, y = self.pos

        pg.draw.rect(screen, (100, 100, 100), (x, y, 200, 10))
        pos = int((self.value - self.min_value) / (self.max_value - self.min_value) * 200)
        pg.draw.rect(screen, (200, 200, 50), (x + pos - 5, y - 5, 10, 20))
        font = pg.font.SysFont(None, 24)
        text = font.render(f"{self.label}: {self.value:.2f}", True, (255,255,255))
        screen.blit(text, (x, y - 25))
        if self.dragging:
            print(x + pos - 5, y - 5)

    def update(self, event):
        x, y = self.pos

        if event.type == pg.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if x <= mx <= x + 200 and y <= my <= y + 10:
                self.dragging = True
        elif event.type == pg.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pg.MOUSEMOTION and self.dragging:
            mx, my = event.pos
            val = (mx - x) / 200
            self.value = max(0, min(1, val)) + self.min_value


pg.init()
screen_size = (240*5, 136*5)
screen = pg.display.set_mode(screen_size, pg.RESIZABLE)
clock = pg.time.Clock()

hsv = HsvServiceVariation('../assets/meme.png')
export_btn = Button((700, 450, 100, 50), "EXPORT", hsv.export)

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            # print(*fd.debug)
            terminate()
        if event.type == pg.VIDEORESIZE:
            screen_size = (event.w, event.h)
        hsv.update(event)
        export_btn.update(event)

    screen.fill((30, 30, 30))
    hsv.draw()
    export_btn.draw()
    pg.display.flip()
    clock.tick(30)
