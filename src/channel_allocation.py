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
        self.histogram_surface = None
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

    def create_histogram(self):
        """
        Создает гистограмму для текущего изображения
        """
        if not self.images or self.selected_image_index >= len(self.images):
            return

        try:
            img = self.images[self.selected_image_index]

            fig, ax = plt.subplots(figsize=(5, 5))

            print(img.shape)
            # contains normalized rbg values
            if abs(int(img[:,:, 0][0][0]) - img[:,:, 0][0][0]) > 0.0001:
                img[:,:] *= 255
                # print(img[:,:,0][0][0])

            if len(img.shape) == 3:  # КПИ цветного изображения
                colors = ['red', 'green', 'blue']
                for i, color in enumerate(colors):
                    ax.hist(img[:, :, i].flatten(), bins=50, alpha=0.7, color=color, density=True)
            else:  # Черно-белое изображение хз
                ax.hist(img.flatten(), bins=50, alpha=0.7, color='gray', density=True)

            ax.set_xlabel('Значение пикселя')
            ax.set_ylabel('Плотность')

            # Сохраняем в память
            fig.canvas.draw()
            buf = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            buf = buf.reshape(fig.canvas.get_width_height()[::-1] + (3,))

            # Конвертируем в pygame surface
            histogram_surf = pygame.surfarray.make_surface(buf.swapaxes(0, 1))
            self.histogram_surface = pygame.transform.scale(
                histogram_surf,
                (int(self.histogram_area.width), int(self.histogram_area.height - 400))
            )

            plt.close(fig)  # Закрываем фигуру для экономии памяти

        except Exception as e:
            print(f"Ошибка создания гистограммы: {e}")
            # Создаем заглушку
            self.histogram_surface = pygame.Surface((int(self.histogram_area.width), 200))
            self.histogram_surface.fill((60, 60, 60))

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
            img_surf = self.image_surfaces[self.selected_image_index]

            # Центрируем изображение в левой области
            img_x = self.images_area.x + (self.images_area.width - img_surf.get_width()) // 2
            img_y = self.images_area.y + 50

            self.screen.blit(img_surf, (img_x, img_y))

            # Информация об изображении
            info_text = f"Изображение {self.selected_image_index + 1}/{len(self.image_surfaces)}"
            text_surf = self.font_medium.render(info_text, True, self.colors['text'])
            self.screen.blit(text_surf, (self.images_area.x + 10, self.images_area.y + 10))

        # Отрисовка гистограммы
        if self.histogram_surface:
            hist_y = self.histogram_area.y + 50
            self.screen.blit(self.histogram_surface, (self.histogram_area.x, hist_y))

        # Заголовок области гистограммы
        hist_title = self.font_medium.render("Гистограмма", True, self.colors['text'])
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
                        self.create_histogram()  # Пересоздаем гистограмму для нового изображения

    def main_loop(self):
        """
        Главный цикл приложения
        """
        # Загружаем изображения
        self.load_images()

        # Создаем начальную гистограмму
        if self.images:
            self.create_histogram()

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