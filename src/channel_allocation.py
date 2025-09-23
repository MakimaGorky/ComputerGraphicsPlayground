import random
import pygame
import os
import numpy as np
import matplotlib.pyplot as plt
from pygame.locals import *

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Image_list = [
    os.path.join(base_dir, "assets", "win1991.jpg"),
    os.path.join(base_dir, "assets", "win2021.jpg"),
    os.path.join(base_dir, "assets", "win2036.jpg"),
    os.path.join(base_dir, "assets", "win2025.jpg"),
    # os.path.join(base_dir, "assets", "win1984.png"),
    # os.path.join(base_dir, "assets", "win2077.jpg"),
]


# Запасные изображения для тестирования
def create_test_image(color, size=(250, 200)):
    """
    Создает тестовое изображение заданного цвета
    """
    surface = pygame.Surface(size)
    surface.fill(color)
    return surface


class App:
    def __init__(self, width=1200, height=800, caption="RageGreedyBoy"):
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
        self.histogram_surfaces = []
        self.selected_image_index = 0
        self.current_image_path = None

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

    def load_images(self):
        """
        Загружает все доступные изображения
        """
        self.image_surfaces = []
        self.images = []

        # Пробуем загрузить изображения из списка
        loaded_count = 0
        for path in Image_list:
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

    def load_single_image(self, path):
        """
        Загружает одно изображение
        """
        try:
            if os.path.exists(path):
                img_surf = pygame.image.load(path).convert()
                scaled_img_surf = pygame.transform.scale(
                    img_surf,
                    (self.thumb_width, self.thumb_height)
                )
                self.image_surfaces.append(scaled_img_surf)

                # Загружаем как numpy array для гистограммы
                try:
                    img_array = plt.imread(path)
                    self.images.append(img_array)
                except:
                    # Если plt.imread не работает, создаем массив из pygame surface
                    img_array = pygame.surfarray.array3d(scaled_img_surf)
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

    def create_histograms(self):
        """
        Создает 4 гистограммы для текущего изображения:
        - 3 отдельные гистограммы для каждого цветового канала
        - 1 совмещенная гистограмма со всеми тремя каналами
        """
        if not self.images or self.selected_image_index >= len(self.images):
            return []

        try:
            img = self.images[self.selected_image_index]

            # Нормализуем значения, если они в диапазоне [0, 1]
            if abs(int(img[:, :, 0][0][0]) - img[:, :, 0][0][0]) > 0.0001:
                img = img.copy()
                img *= 255

            histogram_surfaces = []

            bins = 16

            if len(img.shape) == 3:  # Цветное изображение
                colors = ['red', 'green', 'blue']
                color_names = ['Красный', 'Зеленый', 'Синий']

                # Создаем 3 отдельные гистограммы для каждого канала
                for i, (color, name) in enumerate(zip(colors, color_names)):
                    fig, ax = plt.subplots(figsize=(2, 3))
                    ax.hist(img[:, :, i].flatten(), bins=bins, alpha=0.8, color=color, density=True)
                    ax.set_title(f'{name} канал', fontsize=9)
                    ax.tick_params(axis='both', which='major', labelsize=7)
                    plt.tight_layout()

                    # Конвертируем в pygame surface
                    fig.canvas.draw()
                    buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
                    width, height = fig.canvas.get_width_height()
                    buf = buf.reshape(height, width, 4)  # RGBA формат

                    # Конвертируем в RGB для pygame (убираем альфа-канал)
                    rgb_buf = buf[:, :, :3]
                    histogram_surf = pygame.surfarray.make_surface(rgb_buf.swapaxes(0, 1))

                    # Масштабируем под размер области
                    scaled_surf = pygame.transform.scale(
                        histogram_surf,
                        (int(self.histogram_area.width // 2 - 15), int(self.histogram_area.height // 2 - 40))
                    )
                    histogram_surfaces.append(scaled_surf)
                    plt.close(fig)

                # Создаем совмещенную гистограмму
                fig, ax = plt.subplots(figsize=(2, 3))
                for i, color in enumerate(colors):
                    ax.hist(img[:, :, i].flatten(), bins=bins, alpha=0.6, color=color,
                            density=True, label=color_names[i])

                ax.set_title('Совмещенные каналы', fontsize=9)
                ax.legend(fontsize=7)
                ax.tick_params(axis='both', which='major', labelsize=7)
                plt.tight_layout()

                # Конвертируем в pygame surface
                fig.canvas.draw()
                buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
                width, height = fig.canvas.get_width_height()
                buf = buf.reshape(height, width, 4)  # RGBA формат

                # Конвертируем в RGB для pygame (убираем альфа-канал)
                rgb_buf = buf[:, :, :3]
                histogram_surf = pygame.surfarray.make_surface(rgb_buf.swapaxes(0, 1))

                scaled_surf = pygame.transform.scale(
                    histogram_surf,
                    (int(self.histogram_area.width // 2 - 15), int(self.histogram_area.height // 2 - 40))
                )
                histogram_surfaces.append(scaled_surf)
                plt.close(fig)

            return histogram_surfaces

        except Exception as e:
            print(f"Ошибка создания гистограмм: {e}")
            # Создаем заглушки
            histogram_surfaces = []
            for i in range(4):
                fallback_surf = pygame.Surface((int(self.histogram_area.width // 2 - 15),
                                                int(self.histogram_area.height // 2 - 40)))
                fallback_surf.fill((60, 60, 60))
                histogram_surfaces.append(fallback_surf)
            return histogram_surfaces

    def process_image(self, img_array, process_type="original"):
        """
        Обрабатывает изображение в зависимости от типа обработки
        Args:
            img_array: numpy array изображения
            process_type: тип обработки ("original", "red", "green", "blue")
        Returns:
            обработанный numpy array
        """

        if process_type == "original":
            return img_array.copy()
        # red -> 0, green -> 1, blue -> 2
        elif process_type == "red":
            processed = img_array.copy()
            if len(processed.shape) == 3:
                processed[:, :, 1] = 0
                processed[:, :, 2] = 0
            plt.imsave(arr=processed, fname=os.path.join(base_dir, "assets", 'red.jpg'))
            return processed
        elif process_type == "green":
            processed = img_array.copy()
            if len(processed.shape) == 3:
                processed[:, :, 0] = 0
                processed[:, :, 2] = 0
            return processed
        elif process_type == "blue":
            processed = img_array.copy()
            if len(processed.shape) == 3:
                processed[:, :, 0] = 0
                processed[:, :, 1] = 0
            return processed
        return img_array.copy()

    def create_processed_surfaces(self):
        """Создает 4 обработанные версии текущего изображения"""
        if not self.images or self.selected_image_index >= len(self.images):
            return []

        base_img = self.images[self.selected_image_index].copy()
        process_types = ["original", "red", "green", "blue"]
        processed_surfaces = []

        for process_type in process_types:
            processed_img = self.process_image(base_img, process_type)

            try:
                # Создаем pygame surface через разные подходы
                if processed_img.shape[2] == 3:  # RGB
                    surf = pygame.surfarray.make_surface(processed_img.swapaxes(0, 1))
                else:  # RGBA
                    surf = pygame.surfarray.make_surface(processed_img[:, :, :3].swapaxes(0, 1))

                scaled_surf = pygame.transform.scale(surf, (self.thumb_width, self.thumb_height))
                processed_surfaces.append(scaled_surf)

            except Exception as e:
                print(f"Ошибка создания surface для {process_type}: {e}")
                print(f"Форма массива: {processed_img.shape}, тип: {processed_img.dtype}")

                # Создаем заглушку
                fallback_surf = pygame.Surface((self.thumb_width, self.thumb_height))
                fallback_surf.fill((100, 100, 100))  # Серый цвет
                processed_surfaces.append(fallback_surf)

        return processed_surfaces

    def draw_interface(self):
        """
        Отрисовка интерфейса
        """
        # Очищаем экран
        self.screen.fill(self.colors['background'])

        # Рисуем рамки областей
        pygame.draw.rect(self.screen, self.colors['border'], self.images_area, 2)
        pygame.draw.rect(self.screen, self.colors['border'], self.histogram_area, 2)

        # Отрисовка текущего изображения
        if self.image_surfaces and self.selected_image_index < len(self.image_surfaces):
            processed_surfaces = self.create_processed_surfaces()

            if processed_surfaces:
                # Заголовки для каждой версии
                titles = ["Оригинал", "Только Красный", "Только Зеленый", "Только Синий"]

                # Располагаем изображения в сетке 2x2
                for i, (surf, title) in enumerate(zip(processed_surfaces, titles)):
                    row = i // 2
                    col = i % 2

                    x = self.images_area.x + 10 + col * (self.thumb_width + 20)
                    y = self.images_area.y + 40 + row * (self.thumb_height + 40)

                    # Рисуем изображение
                    self.screen.blit(surf, (x, y))

                    # Рисуем заголовок
                    title_surf = self.font_small.render(title, True, self.colors['text'])
                    self.screen.blit(title_surf, (x, y - 20))

            # Информация об изображении
            info_text = f"Изображение {self.selected_image_index + 1}/{len(self.image_surfaces)}"
            text_surf = self.font_medium.render(info_text, True, self.colors['text'])
            self.screen.blit(text_surf, (self.images_area.x + 10, self.images_area.y + 10))

            # Отрисовка четырех гистограмм
            if self.histogram_surfaces:
                histogram_titles = ["Красный канал", "Зеленый канал", "Синий канал", "Совмещенная"]

                for i, (hist_surf, title) in enumerate(zip(self.histogram_surfaces, histogram_titles)):
                    row = i // 2
                    col = i % 2

                    x = self.histogram_area.x + 5 + col * (hist_surf.get_width() + 10)
                    y = self.histogram_area.y + 35 + row * (hist_surf.get_height() + 25)

                    # Рисуем гистограмму
                    self.screen.blit(hist_surf, (x, y))

                    # Рисуем заголовок
                    title_surf = self.font_small.render(title, True, self.colors['text'])
                    self.screen.blit(title_surf, (x, y - 15))

            # Заголовок области гистограммы
            hist_title = self.font_medium.render("Гистограммы каналов (Цвет / Вероятность)", True, self.colors['text'])
            self.screen.blit(hist_title, (self.histogram_area.x + 10, self.histogram_area.y + 10))

        # Инструкции
        instructions = [
            "ESC - выход",
            "1,2,3,4 - выбор изображения",
            "Используйте клавиши для навигации"
        ]

        y_offset = self.height - 80
        for instruction in instructions:
            text_surf = self.font_small.render(instruction, True, self.colors['text'])
            self.screen.blit(text_surf, (10, y_offset))
            y_offset += 20

    def handle_events(self):
        """
        Обработка событий
        """
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key in [K_1, K_2, K_3, K_4]:
                    new_index = event.key - K_1
                    if new_index < len(self.image_surfaces):
                        self.selected_image_index = new_index
                        self.histogram_surfaces = self.create_histograms()  # Пересоздаем гистограммы

    def main_loop(self):
        """
        Главный цикл приложения
        """
        # Загружаем изображения
        self.load_images()

        # Создаем начальные гистограммы
        if self.images:
            self.histogram_surfaces = self.create_histograms()

        self.running = True
        clock = pygame.time.Clock()

        while self.running:
            self.handle_events()
            self.draw_interface()  # Добавили отрисовку!
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


if __name__ == '__main__':
    app = App()
    app.main_loop()