
import pygame as pg
import numpy as np
import os  # просто будь собой бро


class ImagesLoader:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(base_dir, "assets")

        # Получаем список всех файлов в папке assets
        self.image_list = [
            os.path.join(assets_dir, filename)
            for filename in os.listdir(assets_dir)
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))  # Фильтруем только изображения
        ]
        # self.image_list = [
        #     os.path.join(base_dir, "assets", "house1.jpg"),
        #     os.path.join(base_dir, "assets", "house2.jpg"),
        #     os.path.join(base_dir, "assets", "house3.jpg"),
        #     os.path.join(base_dir, "assets", "house4.jpg"),
        # ]

        self.thumb_width = 400
        self.thumb_height = 400

        self.image_surfaces = []
        self.images = []
        self.load_images()

        self.selected_image_index = 0


        # Цвета
        self.colors = {
            'background': (40, 44, 52),
            'panel': (30, 34, 42),
            'text': (220, 220, 220),
            'border': (80, 85, 95),
            'highlight': (97, 175, 239),
            'button': (150,150,250)
        }

        # Шрифты
        self.font_large = pg.font.Font(None, 32)
        self.font_medium = pg.font.Font(None, 24)
        self.font_small = pg.font.Font(None, 18)

        # Кнопки
        self.margin = 20
        self.buttons_panel_width = 70
        self.buttons_panel_height = 30
        # self.panel_width = self.width - 2 * self.margin
        # self.panel_height = self.height - self.buttons_panel_height - 3 * self.margin
        self.button_prev = pg.Rect(
            self.margin,
            self.margin,
            self.buttons_panel_width * 0.5 - 5,
            self.buttons_panel_height
            )
        self.button_next = pg.Rect(
            self.margin + self.buttons_panel_width * 0.5 + 5,
            self.margin,
            self.buttons_panel_width * 0.5 - 5,
            self.buttons_panel_height
            )
        self.have_changed = False

    def load_single_image(self, path):
        """
        Загружает одно изображение
        """
        try:
            if os.path.exists(path):
                img_surf = pg.image.load(path).convert()
                scaled_img_surf = pg.transform.scale(
                    img_surf,
                    (self.thumb_width, self.thumb_height)
                )
                self.image_surfaces.append(scaled_img_surf)

                # Загружаем как numpy array для гистограммы
                try:
                    img_array = plt.imread(path)
                    self.images.append(img_array)
                except:
                    # Если plt.imread не работает, создаем массив из pg surface
                    img_array = pg.surfarray.array3d(scaled_img_surf)
                    img_array = np.transpose(img_array, (1, 0, 2))  # Поворачиваем массив
                    self.images.append(img_array)

                print(f"Загружено изображение: {os.path.basename(path)}")
                return True
            else:
                print(f"Файл не найден: {path}")
                return False
        except Exception as e:
            print(f"Ошибка загрузки {path}: {e}")
            return False

    def load_images(self):
        """
        Загружает все доступные изображения
        """

        # Пробуем загрузить изображения из списка
        loaded_count = 0
        for path in self.image_list:
            if self.load_single_image(path):
                loaded_count += 1

        # Если не удалось загрузить изображения, создаем тестовые
        if loaded_count == 0:
            print("Не найдены файлы изображений, создаем тестовые изображения")
            test_colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]
            for i, color in enumerate(test_colors):
                test_surface = create_test_image(color, (self.thumb_width, self.thumb_height))
                self.image_surfaces.append(test_surface)
                # Создаем fake array для тестового изображения
                fake_array = np.random.randint(0, 256, (self.thumb_height, self.thumb_width, 3), dtype=np.uint8)
                self.images.append(fake_array)
                print(f"Создано тестовое изображение {i + 1}")

    def collide(self, point, collision_box):
        x_col = (collision_box.x <= point[0]) and (collision_box.x + collision_box.width >= point[0])
        y_col = (collision_box.y <= point[1]) and (collision_box.y + collision_box.height >= point[1])
        return x_col and y_col

    def draw(self):
        """
        Рисуем кнопки
        """
        pg.draw.rect(screen, self.colors['button'], self.button_prev, border_radius=8)
        text = "<"
        text_surf = self.font_large.render(text, True, self.colors['text'])
        screen.blit(text_surf, (self.button_prev.x + 8, self.button_prev.y + 2))  

        pg.draw.rect(screen, self.colors['button'], self.button_next, border_radius=8)
        text = ">"
        text_surf = self.font_large.render(text, True, self.colors['text'])
        screen.blit(text_surf, (self.button_next.x + 10, self.button_next.y + 2))

    def update(self, event):
        self.have_changed = False
        if event.type == pg.MOUSEBUTTONDOWN:
            self.have_changed = True
            if self.collide(event.pos,self.button_prev):
                self.change_selected_image_index(-1)
            elif self.collide(event.pos,self.button_next):
                self.change_selected_image_index(1)
            else:
                self.have_changed = False

    def change_selected_image_index(self, changer):
        mod = len(self.image_surfaces)
        self.selected_image_index = (mod + self.selected_image_index + changer) % mod

    def get_image(self):
        return self.image_surfaces[self.selected_image_index]



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

    h[rmask] = bc[rmask] - gc[rmask] + 6
    h[gmask] = rc[gmask] - bc[gmask] + 2
    h[bmask] = gc[bmask] - rc[bmask] + 4
    h = (h / 6.0) % 1.0

    return np.stack([h, s, v], axis=-1)


def hsv2rgb(hsv):
    h, s, v = hsv[...,0], hsv[...,1], hsv[...,2]
    i = np.floor(h * 6).astype(int)  # номер сектора
    f = h * 6 - i  # дробная часть сектора
    p = v * (1 - s)  # V_min минимальное значение канала
    q = v * (1 - f * s)  # V_dec  промежуточное значение 
    t = v * (1 - (1 - f) * s)  # V_inc промежуточное значение, но в другую сторону
    rgb = np.zeros_like(hsv)

    rgb[...,0] = np.choose(i % 6, [v, q, p, p, t, v])
    rgb[...,1] = np.choose(i % 6, [t, v, v, q, p, p])
    rgb[...,2] = np.choose(i % 6, [p, p, t, v, v, q])
    return rgb


class HsvServiceVariation:
    def __init__(self):
        self.images_loager = ImagesLoader()
        self.init_image()
        # self.image = self.images_loager.get_image()
        # # self.image = pg.image.load(image_path).convert()
        # self.rgb = pg.surfarray.array3d(self.image).astype(np.float32) / 255.0
        # self.hsv = rgb2hsv(self.rgb)
        # self.h_shift = 0.0
        # self.s_shift = 0.0
        # self.v_shift = 0.0

        self.position = (30, 100)
        self.h_slider = Slider('H', 0, 1, 650, 300)
        self.s_slider = Slider('S', -0.5, 0.5, 650, 350)
        self.v_slider = Slider('V', -0.5, 0.5, 650, 400)

        self.surf = pg.surfarray.make_surface(np.transpose(self.rgb, (1,0,2)).swapaxes(0,1))

    def init_image(self):
        self.image = self.images_loager.get_image()
        # self.image = pg.image.load(image_path).convert()
        self.rgb = pg.surfarray.array3d(self.image).astype(np.float32) / 255.0
        self.hsv = rgb2hsv(self.rgb)
        self.h_shift = 0.0
        self.s_shift = 0.0
        self.v_shift = 0.0


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
        self.images_loager.draw()

    def update(self, event):
        self.h_slider.update(event)
        self.s_slider.update(event)
        self.v_slider.update(event)

        self.images_loager.update(event)

        self.h_shift = self.h_slider.value
        self.s_shift = self.s_slider.value
        self.v_shift = self.v_slider.value

        if self.images_loager.have_changed:
            self.init_image()


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
        # if self.dragging:
        #     print(x + pos - 5, y - 5)

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

# hsv = HsvServiceVariation('../assets/meme.png')
hsv = HsvServiceVariation()
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
