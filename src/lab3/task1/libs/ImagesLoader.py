
import pygame as pg
import numpy as np
import os  # просто будь собой бро
import sys  # просто будь собой бро
from Button import *


class ImagesLoader:
    def __init__(self, screen, assets_path="../../../assets"):
        self.screen = screen
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(base_dir, assets_path)

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
        pg.draw.rect(self.screen, self.colors['button'], self.button_prev, border_radius=8)
        text = "<"
        text_surf = self.font_large.render(text, True, self.colors['text'])
        self.screen.blit(text_surf, (self.button_prev.x + 8, self.button_prev.y + 2))  

        pg.draw.rect(self.screen, self.colors['button'], self.button_next, border_radius=8)
        text = ">"
        text_surf = self.font_large.render(text, True, self.colors['text'])
        self.screen.blit(text_surf, (self.button_next.x + 10, self.button_next.y + 2))

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


if __name__ == '__main__':
    pg.init()
    screen_size = (240*5, 136*5)
    screen = pg.display.set_mode(screen_size, pg.RESIZABLE)
    clock = pg.time.Clock()

    images_loader = ImagesLoader(screen)
    image = images_loader.get_image()
    # surf = pg.surfarray.make_surface(np.transpose(image, (1,0,2)).swapaxes(0,1))

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                # print(*fd.debug)
                terminate()
            if event.type == pg.VIDEORESIZE:
                screen_size = (event.w, event.h)
            images_loader.update(event)
            if images_loader.have_changed:
                image = images_loader.get_image()
                # surf = pg.surfarray.make_surface(np.transpose(image, (1,0,2)).swapaxes(0,1))

        screen.fill((30, 30, 30))
        images_loader.draw()
        screen.blit(image, (100, 100))
        pg.display.flip()
        clock.tick(30)
