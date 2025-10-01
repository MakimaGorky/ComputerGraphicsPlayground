
from a import *

def load_single_image_like_get_image(path, thumb_width=400, thumb_height=400):
    """
    Загружает изображение и возвращает pygame.Surface в том же виде, что get_image().
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")

    # Загружаем изображение через pygame
    img_surf = pg.image.load(path)
    scaled_img_surf = pg.transform.scale(img_surf, (thumb_width, thumb_height))
    
    return scaled_img_surf


IMAGE_FROM = load_single_image_like_get_image("../../../assets/meme.png", thumb_width=400, thumb_height=400)
def from_image(x, y):
    width, height = IMAGE_FROM.get_size()
    cx, cy = CENTER
    nx = -cx + width // 2 + x
    ny = -cy + height // 2 + y
    if 0 <= nx < width and 0 <= ny < height:
        return IMAGE_FROM.get_at((nx, ny))
    return (0, 0, 0)


if __name__ == '__main__':
    pg.init()
    screen_size = (240*5, 136*5)
    screen = pg.display.set_mode(screen_size, pg.RESIZABLE)
    clock = pg.time.Clock()

    filler = Filler(screen)

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                # print(*fd.debug)
                pg.quit()
                sys.exit()
            if event.type == pg.VIDEORESIZE:
                screen_size = (event.w, event.h)
            filler.update(event)
            # if images_loader.have_changed:
            #     image = images_loader.get_image()
                # surf = pg.surfarray.make_surface(np.transpose(image, (1,0,2)).swapaxes(0,1))

        if filler.have_clicked:
            CENTER = filler.have_clicked_at[0], filler.have_clicked_at[1]
            filler.run(from_image)

        screen.fill((30, 30, 30))
        filler.draw()
        # images_loader.draw()
        # screen.blit(image, (100, 100))
        pg.display.flip()
        clock.tick(20)
