
import pygame as pg
import numpy as np


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
    i_mod = i % 6

    rgb[...,0] = np.choose(i_mod, [v, q, p, p, t, v])
    rgb[...,1] = np.choose(i_mod, [t, v, v, q, p, p])
    rgb[...,2] = np.choose(i_mod, [p, p, t, v, v, q])
    return rgb


class HsvServiceVariation:
    def __init__(self, image_path):
        self.image = pg.image.load(image_path).convert()
        self.rgb = pygame.surfarray.array3d(self.image).astype(np.float32) / 255.0
        self.hsv = rgb2hsv(self.rgb)
        self.h_shift = 0.0
        self.s_shift = 0.0
        self.v_shift = 0.0

        self.position = (0.1, 0.1)  # доля экрана


    def draw(self):
        x = screen_size[0] * self.position[0]
        y = screen_size[1] * self.position[1]

        hsv = self.hsv.copy()
        hsv[...,0] = (hsv[...,0] + self.h_shift) % 1.0
        hsv[...,1] = np.clip(hsv[...,1] + self.s_shift, 0, 1)
        hsv[...,2] = np.clip(hsv[...,2] + self.v_shift, 0, 1)
        rgb = (hsv2rgb(hsv_mod) * 255).astype(np.uint8)
        surf = pygame.surfarray.make_surface(np.transpose(rgb, (1,0,2)))

        screen.blit(surf, (x, y))


class Slider:
    def __init__(self, label, value, min_value, max_value, x, y):
        self.label = label
        self.value = value
        self.min_value = min_value
        self.max_value = max_value

        self.pos = (x, y)

    def draw(self):
        


pg.init()
screen_size = (240*5, 136*5)
screen = pg.display.set_mode(screen_size, pg.RESIZABLE)
clock = pg.time.Clock()

hsv = HsvServiceVariation('../assets/meme.png')

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            # print(*fd.debug)
            terminate()
        if event.type == pg.VIDEORESIZE:
            screen_size = (event.w, event.h)
    hsv.draw()
    pg.display.flip()
    clock.tick(30)
