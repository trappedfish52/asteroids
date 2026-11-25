"""Самостоятельно нарисованные изображения и тайловая анимация взрыва."""
import math
import random
import pygame
from settings import (
    WIDTH, HEIGHT, SPACE_COLOR, BACKGROUND_ALPHA,
    EXPLOSION_FRAMES, TILE_SIZE,
)


def make_background():
    """Создать неподвижное изображение звёздного неба."""
    image = pygame.Surface((WIDTH, HEIGHT))
    image.fill(SPACE_COLOR)
    rng = random.Random(42)
    for _ in range(140):
        point = rng.randrange(WIDTH), rng.randrange(HEIGHT)
        value = rng.randint(65, 180)
        pygame.draw.circle(image, (value, value, value), point, 1)
    return image


def make_layer():
    """Создать прозрачное изображение декоративных астероидов."""
    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    rng = random.Random(24)
    for _ in range(12):
        pos = rng.randrange(50, WIDTH - 50), rng.randrange(50, HEIGHT - 50)
        radius = rng.randint(15, 45)
        pygame.draw.circle(layer, (120, 145, 180, BACKGROUND_ALPHA),
                           pos, radius)
        pygame.draw.circle(layer, (30, 45, 65, BACKGROUND_ALPHA),
                           (pos[0] - 4, pos[1] - 5), radius // 3)
    return layer


def make_ship(thrust=False):
    """Нарисовать отдельное изображение корабля с двигателем или без."""
    image = pygame.Surface((64, 64), pygame.SRCALPHA)
    if thrust:
        pygame.draw.polygon(image, (255, 152, 50),
                            [(15, 25), (1, 32), (15, 39)])
    pygame.draw.polygon(image, (115, 220, 245),
                        [(52, 32), (14, 14), (22, 32), (14, 50)], 2)
    pygame.draw.circle(image, (210, 245, 255), (32, 32), 4)
    return image


def make_explosions():
    """Создать горизонтальный спрайт-лист с кадрами расширения и угасания."""
    sheet = pygame.Surface((TILE_SIZE * EXPLOSION_FRAMES, TILE_SIZE),
                           pygame.SRCALPHA)
    for frame in range(EXPLOSION_FRAMES):
        progress = frame / EXPLOSION_FRAMES
        center = frame * TILE_SIZE + TILE_SIZE // 2, TILE_SIZE // 2
        radius = int(5 + 39 * progress)
        alpha = int(255 * (1 - progress))
        pygame.draw.circle(sheet, (255, 100, 30, alpha), center, radius)
        pygame.draw.circle(sheet, (255, 225, 115, alpha), center,
                           max(1, radius // 2))
        for ray in range(8):
            angle = ray * math.tau / 8
            point = (center[0] + int(math.cos(angle) * radius),
                     center[1] + int(math.sin(angle) * radius))
            pygame.draw.circle(sheet, (255, 205, 80, alpha), point, 3)
    return sheet


def wrap_blit(screen, image, x, y):
    """Рисовать копии по краям, чтобы объект не обрезался на торе."""
    for dx in (-WIDTH, 0, WIDTH):
        for dy in (-HEIGHT, 0, HEIGHT):
            rect = image.get_rect(center=(round(x + dx), round(y + dy)))
            if rect.colliderect(screen.get_rect()):
                screen.blit(image, rect)


def draw_asteroid(screen, rock):
    """Нарисовать вращающийся многоугольный астероид."""
    size = int(rock.radius * 2 + 6)
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    points = []
    for index, factor in enumerate(rock.shape):
        angle = math.radians(rock.angle) + index * math.tau / 10
        points.append((size / 2 + math.cos(angle) * rock.radius * factor,
                       size / 2 + math.sin(angle) * rock.radius * factor))
    pygame.draw.polygon(image, (56, 66, 88), points)
    pygame.draw.polygon(image, (163, 180, 201), points, 2)
    wrap_blit(screen, image, rock.x, rock.y)
