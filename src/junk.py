import random

import pygame
import os
import numpy as np
import matplotlib.pyplot as plt
from pygame.locals import *

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Image_list = [
    os.path.join(base_dir, "assets", "win1984.png"),
    os.path.join(base_dir, "assets", "win1991.jpg"),
    os.path.join(base_dir, "assets", "win2021.jpg"),
    os.path.join(base_dir, "assets", "win2036.jpg"),
]


class App:
    def __init__(self, width=800, height=600, caption="RageGreedyBoy"):
        """
        Sample App
        Args:
            width: очевидно
            height: нетрудно догадаться
            caption: оставим читателю, как упражнение

        :return: 😂😂😂
        """
        pygame.init()
        self.width, self.height = width, height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(caption)

        # Цвета
        self.colors = {
            'background': (40, 44, 52),
            'panel': (30, 34, 42),
            'text': (220, 220, 220),
            'border': (80, 85, 95),
            'highlight': (97, 175, 239)
        }

        # Шрифты
        self.font_large = pygame.font.Font(None, 32)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)

        # Изображения и данные
        self.images = []
        self.image_size = (200, 150)
        self.image_surfaces = []
        self.histogram_surface = None
        self.selected_image_index = 0

        # Позиции и размеры
        self.margin = 20
        self.panel_width = self.width - 2 * self.margin
        self.panel_height = self.height - 2 * self.margin

        self.images_area = pygame.Rect(
            self.margin,
            self.margin,
            self.panel_width * 0.6,
            self.panel_height
        )

        # Область для гистограммы (правая часть)
        self.histogram_area = pygame.Rect(
            self.margin + self.panel_width * 0.6 + 10,
            self.margin,
            self.panel_width * 0.4 - 10,
            self.panel_height
        )

        # Размеры миниатюр изображений
        self.thumb_width = 250
        self.thumb_height = 200

        # Флаги состояния
        self.running = False

    def setup_layout(self):
        """
        Настройка layout приложения
        """



    def load_image(self, path):
        self.image_surfaces = []

        try:
            if os.path.exists(path):
                img_surf = pygame.image.load(path).convert()
                scaled_img_surf = pygame.transform.scale(
                    img_surf,
                    (self.thumb_width, self.thumb_height)
                )
                self.image_surfaces.append(scaled_img_surf)

                img_array = plt.imread(path)
                self.images.append(img_array)

                print(f"Загружено изображение: {os.path.basename(path)}")
            else:
                print(f"Файл не найден: {path}")
        except Exception as e:
            print(f"Cringy thing {e}")

        if not self.images:
            print("Не загружено ни одного изображения!")

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            # elif event.type == MOUSEBUTTONDOWN:
                # if event.button == 1:  # Левая кнопка мыши
                    # self.handle_mouse_click(event.pos)
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key in [K_1, K_2, K_3, K_4]:
                    self.selected_image_index = event.key - K_1

    def main_loop(self):
        """
        Главный цикл?
        """
        self.load_image(Image_list[random.randint(0, len(Image_list) - 1)])

        self.running = True
        # Основной цикл
        clock = pygame.time.Clock()
        while self.running:
            self.handle_events()
            pygame.display.flip()
            clock.tick(60)


if __name__ == '__main__':
    app = App()
    app.main_loop()








class ImageHistogramApp:
    def __init__(self, width=1200, height=700, title="Image Viewer with Histogram"):
        """
        Инициализация приложения

        Args:
            width (int): ширина окна
            height (int): высота окна
            title (str): заголовок окна
        """
        pygame.init()
        self.width = width
        self.height = height
        self.title = title
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)

        # Цвета
        self.colors = {
            'background': (40, 44, 52),
            'panel': (30, 34, 42),
            'text': (220, 220, 220),
            'border': (80, 85, 95),
            'highlight': (97, 175, 239)
        }

        # Шрифты
        self.font_large = pygame.font.Font(None, 32)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)

        # Изображения и данные
        self.images = []
        self.image_surfaces = []
        self.histogram_surface = None
        self.selected_image_index = 0

        # Позиции и размеры
        self.setup_layout()

        # Флаги состояния
        self.running = True

    def setup_layout(self):
        """Настройка layout приложения"""
        self.margin = 20
        self.panel_width = self.width - 2 * self.margin
        self.panel_height = self.height - 2 * self.margin

        # Область для изображений (левая часть)
        self.images_area = pygame.Rect(
            self.margin,
            self.margin,
            self.panel_width * 0.6,
            self.panel_height
        )

        # Область для гистограммы (правая часть)
        self.histogram_area = pygame.Rect(
            self.margin + self.panel_width * 0.6 + 10,
            self.margin,
            self.panel_width * 0.4 - 10,
            self.panel_height
        )

        # Размеры миниатюр изображений
        self.thumb_width = 250
        self.thumb_height = 200

    def load_images(self, image_paths):
        """
        Загрузка изображений из указанных путей

        Args:
            image_paths (list): список путей к изображениям
        """
        self.images = []
        self.image_surfaces = []

        for i, path in enumerate(image_paths):
            try:
                if os.path.exists(path):
                    # Загрузка изображения для Pygame
                    img_surface = pygame.image.load(path).convert()
                    # Масштабирование
                    scaled_surface = pygame.transform.scale(
                        img_surface,
                        (self.thumb_width, self.thumb_height)
                    )
                    self.image_surfaces.append(scaled_surface)

                    # Загрузка изображения для анализа (для гистограммы)
                    img_array = plt.imread(path)
                    self.images.append(img_array)

                    print(f"Загружено изображение {i + 1}: {os.path.basename(path)}")
                else:
                    print(f"Файл не найден: {path}")
                    # Создание placeholder
                    self.create_placeholder_image(i)

            except Exception as e:
                print(f"Ошибка загрузки изображения {path}: {e}")
                self.create_placeholder_image(i)

        if not self.images:
            print("Не загружено ни одного изображения!")

    def create_placeholder_image(self, index):
        """Создание placeholder изображения"""
        # Surface для Pygame
        surf = pygame.Surface((self.thumb_width, self.thumb_height))
        surf.fill((70, 70, 70))
        font = pygame.font.Font(None, 20)
        text = font.render(f"Image {index + 1} not found", True, (200, 200, 200))
        text_rect = text.get_rect(center=(self.thumb_width // 2, self.thumb_height // 2))
        surf.blit(text, text_rect)
        self.image_surfaces.append(surf)

        # Массив для анализа (серый квадрат)
        self.images.append(np.full((100, 100), 128, dtype=np.uint8))

    def create_histogram(self, image_index):
        """
        Создание гистограммы для выбранного изображения

        Args:
            image_index (int): индекс изображения
        """
        if not self.images or image_index >= len(self.images):
            return None

        img_array = self.images[image_index]

        # Преобразование в grayscale если нужно
        if len(img_array.shape) == 3:
            if img_array.shape[2] == 4:  # RGBA
                img_gray = np.dot(img_array[..., :3], [0.2989, 0.5870, 0.1140])
            else:  # RGB
                img_gray = np.dot(img_array, [0.2989, 0.5870, 0.1140])
        else:
            img_gray = img_array

        # Нормализация
        img_gray = (img_gray - img_gray.min()) / (img_gray.max() - img_gray.min()) * 255
        img_gray = img_gray.astype(np.uint8)

        # Создание гистограммы
        plt.figure(figsize=(6, 4), facecolor='#2c313c')
        plt.hist(img_gray.flatten(), bins=64, range=(0, 255),
                 color='#61afef', alpha=0.7, edgecolor='#3b404b')

        plt.title(f'Histogram - Image {image_index + 1}',
                  color='#dcdfe4', fontsize=12, pad=10)
        plt.xlabel('Intensity', color='#dcdfe4')
        plt.ylabel('Frequency', color='#dcdfe4')

        # Стилизация
        ax = plt.gca()
        ax.set_facecolor('#2c313c')
        ax.tick_params(colors='#dcdfe4')
        ax.spines['bottom'].set_color('#5c6370')
        ax.spines['top'].set_color('#5c6370')
        ax.spines['right'].set_color('#5c6370')
        ax.spines['left'].set_color('#5c6370')

        plt.tight_layout()

        # Сохранение во временный файл
        temp_path = os.path.join(os.path.dirname(__file__), "temp_histogram.png")
        plt.savefig(temp_path, facecolor='#2c313c', edgecolor='none')
        plt.close()

        # Загрузка в Pygame
        if os.path.exists(temp_path):
            hist_surface = pygame.image.load(temp_path).convert()
            # Масштабирование под область гистограммы
            scaled_hist = pygame.transform.scale(
                hist_surface,
                (self.histogram_area.width - 20, self.histogram_area.height - 60)
            )
            return scaled_hist

        return None

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка мыши
                    self.handle_mouse_click(event.pos)
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key in [K_1, K_2, K_3, K_4]:
                    self.selected_image_index = event.key - K_1
                    self.update_histogram()

    def handle_mouse_click(self, pos):
        """Обработка клика мыши для выбора изображения"""
        for i in range(min(4, len(self.image_surfaces))):
            img_rect = self.get_image_rect(i)
            if img_rect.collidepoint(pos):
                self.selected_image_index = i
                self.update_histogram()
                break

    def get_image_rect(self, index):
        """Получение прямоугольника для изображения по индексу"""
        if index >= 4:
            return None

        rows, cols = 2, 2
        row = index // cols
        col = index % cols

        spacing = 20
        total_width = 2 * self.thumb_width + spacing
        total_height = 2 * self.thumb_height + spacing

        start_x = self.images_area.x + (self.images_area.width - total_width) // 2
        start_y = self.images_area.y + (self.images_area.height - total_height) // 2

        x = start_x + col * (self.thumb_width + spacing)
        y = start_y + row * (self.thumb_height + spacing)

        return pygame.Rect(x, y, self.thumb_width, self.thumb_height)

    def update_histogram(self):
        """Обновление гистограммы для выбранного изображения"""
        self.histogram_surface = self.create_histogram(self.selected_image_index)

    def draw(self):
        """Отрисовка интерфейса"""
        # Очистка экрана
        self.screen.fill(self.colors['background'])

        # Отрисовка области изображений
        pygame.draw.rect(self.screen, self.colors['panel'], self.images_area, border_radius=10)
        pygame.draw.rect(self.screen, self.colors['border'], self.images_area, 2, border_radius=10)

        # Отрисовка изображений
        for i in range(min(4, len(self.image_surfaces))):
            img_rect = self.get_image_rect(i)
            if img_rect:
                # Рамка для выбранного изображения
                if i == self.selected_image_index:
                    pygame.draw.rect(self.screen, self.colors['highlight'],
                                     img_rect.inflate(10, 10), 3, border_radius=5)

                # Изображение
                self.screen.blit(self.image_surfaces[i], img_rect)

                # Номер изображения
                text = self.font_medium.render(f"Image {i + 1}", True, self.colors['text'])
                self.screen.blit(text, (img_rect.x, img_rect.y - 25))

        # Отрисовка области гистограммы
        pygame.draw.rect(self.screen, self.colors['panel'], self.histogram_area, border_radius=10)
        pygame.draw.rect(self.screen, self.colors['border'], self.histogram_area, 2, border_radius=10)

        # Заголовок гистограммы
        hist_title = self.font_large.render("Histogram", True, self.colors['text'])
        self.screen.blit(hist_title, (self.histogram_area.x + 20, self.histogram_area.y + 15))

        # Отрисовка гистограммы
        if self.histogram_surface:
            hist_x = self.histogram_area.x + 10
            hist_y = self.histogram_area.y + 50
            self.screen.blit(self.histogram_surface, (hist_x, hist_y))

        # Инструкции
        instructions = [
            "Click on image to select",
            "Press 1-4 to select image",
            "ESC to exit"
        ]

        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, self.colors['text'])
            self.screen.blit(text, (self.histogram_area.x + 20,
                                    self.histogram_area.y + self.histogram_area.height - 60 + i * 20))

    def run(self, image_paths):
        """
        Запуск приложения

        Args:
            image_paths (list): список путей к изображениям
        """
        # Загрузка изображений
        self.load_images(image_paths)

        # Создание начальной гистограммы
        self.update_histogram()

        # Основной цикл
        clock = pygame.time.Clock()
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            clock.tick(60)

        # Очистка
        self.cleanup()

    def cleanup(self):
        """Очистка ресурсов"""
        # Удаление временного файла гистограммы
        temp_path = os.path.join(os.path.dirname(__file__), "temp_histogram.png")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

        pygame.quit()


# Пример использования
# if __name__ == "__main__":
#     # Получение текущей директории
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#
#     # Пути к изображениям (относительно текущей папки)
#     image_paths = [
#         os.path.join(current_dir, "images", "image1.jpg"),
#         os.path.join(current_dir, "images", "image2.jpg"),
#         os.path.join(current_dir, "images", "image3.jpg"),
#         os.path.join(current_dir, "images", "image4.jpg")
#     ]
#
#     # Создание и запуск приложения
#     app = ImageHistogramApp()
#     app.run(image_paths)