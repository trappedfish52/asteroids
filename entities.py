"""Движущиеся объекты и столкновения на тороидальном поле."""
import math
import random
from dataclasses import dataclass

from settings import (
    WIDTH, HEIGHT, ACCELERATION, DRAG, STOP_SPEED, MAX_SPEED,
    ROCKET_SPEED, ROCKET_LIFE, SHIP_RADIUS, ROCKET_RADIUS,
    ROCK_SPEED, ROCK_SPIN, ROCK_RADIUS,
)


def heading(angle):
    """Получить единичный вектор из угла в градусах."""
    radians = math.radians(angle)
    return math.cos(radians), math.sin(radians)


def touches(first, second):
    """Проверить круговые коллизии с учётом соседства противоположных краёв."""
    dx = abs(first.x - second.x) % WIDTH
    dy = abs(first.y - second.y) % HEIGHT
    dx, dy = min(dx, WIDTH - dx), min(dy, HEIGHT - dy)
    return dx * dx + dy * dy <= (first.radius + second.radius) ** 2


@dataclass
class Body:
    """Базовый объект с координатами и линейной/угловой скоростью."""

    x: float
    y: float
    vx: float = 0
    vy: float = 0
    angle: float = 0
    spin: float = 0
    radius: float = 0

    def move(self, dt):
        """Перенести объект через границы без изменения скорости."""
        self.x = (self.x + self.vx * dt) % WIDTH
        self.y = (self.y + self.vy * dt) % HEIGHT
        self.angle = (self.angle + self.spin * dt) % 360


class Ship(Body):
    """Корабль с двигателем и сопротивлением среды."""

    def __init__(self):
        """Возродить корабль неподвижным в центре поля."""
        super().__init__(WIDTH / 2, HEIGHT / 2, angle=-90,
                         radius=SHIP_RADIUS)

    def update(self, dt, thrust, turn):
        """Изменить ориентацию и скорость, затем передвинуть корабль."""
        self.angle = (self.angle + turn * dt) % 360
        if thrust:
            dx, dy = heading(self.angle)
            self.vx += dx * ACCELERATION * dt
            self.vy += dy * ACCELERATION * dt
            speed = math.hypot(self.vx, self.vy)
            if speed > MAX_SPEED:
                self.vx *= MAX_SPEED / speed
                self.vy *= MAX_SPEED / speed
        else:
            # Экспонента делает сопротивление независимым от частоты кадров.
            factor = math.exp(-DRAG * dt)
            self.vx *= factor
            self.vy *= factor
            if math.hypot(self.vx, self.vy) < STOP_SPEED:
                self.vx = self.vy = 0
        self.move(dt)


class Rocket(Body):
    """Ракета с постоянной скоростью и ограниченным временем жизни."""

    def __init__(self, ship):
        """Создать ракету у носа корабля по направлению его ориентации."""
        dx, dy = heading(ship.angle)
        offset = SHIP_RADIUS + ROCKET_RADIUS
        super().__init__((ship.x + dx * offset) % WIDTH,
                         (ship.y + dy * offset) % HEIGHT,
                         dx * ROCKET_SPEED, dy * ROCKET_SPEED,
                         angle=ship.angle, radius=ROCKET_RADIUS)
        self.life = ROCKET_LIFE

    def update(self, dt):
        """Передвинуть ракету и уменьшить остаток времени жизни."""
        self.move(dt)
        self.life -= dt


class Asteroid(Body):
    """Астероид со случайными скоростями, радиусом и контуром."""

    def __init__(self):
        """Сгенерировать новый астероид в случайной точке поля."""
        dx, dy = heading(random.uniform(0, 360))
        speed = random.uniform(*ROCK_SPEED)
        super().__init__(random.uniform(0, WIDTH), random.uniform(0, HEIGHT),
                         dx * speed, dy * speed, random.uniform(0, 360),
                         random.uniform(*ROCK_SPIN),
                         random.randint(*ROCK_RADIUS))
        self.shape = [random.uniform(0.75, 1) for _ in range(10)]


class Explosion:
    """Положение и возраст взрыва для выбора кадра из тайлового листа."""

    def __init__(self, x, y):
        """Начать анимацию в точке столкновения."""
        self.x, self.y = x, y
        self.age = 0
