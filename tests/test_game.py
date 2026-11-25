"""Проверки физики и игровых состояний без графического дисплея."""
import math
import os
import unittest

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from entities import Body, Rocket, Ship, Asteroid, touches
from settings import WIDTH, HEIGHT, ROCKET_SPEED, ROCKET_LIFE


class PhysicsTests(unittest.TestCase):
    """Движение на торе, коллизии и ограничение дальности ракет."""

    def test_wrap(self):
        """Перенос сохраняет обе скорости."""
        body = Body(WIDTH - 1, 10, 10, 0, spin=30)
        body.move(1)
        self.assertEqual((body.x, body.vx, body.spin), (9, 10, 30))

    def test_seam_collision(self):
        """Объекты сталкиваются через противоположные края."""
        self.assertTrue(touches(Body(1, 100, radius=5),
                                Body(WIDTH - 1, 100, radius=5)))

    def test_rocket_range(self):
        """Ракета не пересекает поле за время жизни."""
        self.assertLess(ROCKET_SPEED * ROCKET_LIFE, min(WIDTH, HEIGHT))
        ship = Ship()
        ship.vx = 300
        rocket = Rocket(ship)
        self.assertAlmostEqual(math.hypot(rocket.vx, rocket.vy),
                               ROCKET_SPEED)
        rocket.update(ROCKET_LIFE)
        self.assertLessEqual(rocket.life, 0)

    def test_drag(self):
        """Без тяги корабль полностью останавливается."""
        ship = Ship()
        ship.vx = 50
        for _ in range(200):
            ship.update(0.05, False, 0)
        self.assertEqual(ship.vx, 0)


@unittest.skipUnless(os.getenv("RUN_GRAPHICS") == "1",
                     "Графические тесты: задайте RUN_GRAPHICS=1")
class GameTests(unittest.TestCase):
    """Игровые состояния и отрисовка с виртуальным дисплеем."""

    def setUp(self):
        """Создать игру для независимого теста."""
        from main import Game
        self.game = Game()

    def tearDown(self):
        """Закрыть виртуальный экран."""
        import pygame
        pygame.quit()

    def test_lives(self):
        """Четвёртое столкновение при нуле жизней завершает игру."""
        self.game.start()
        for expected in (2, 1, 0):
            rock = Asteroid()
            self.game.rocks.append(rock)
            self.game.hit_ship(rock)
            self.assertEqual(self.game.lives, expected)
            self.assertTrue(self.game.active)
            self.assertEqual(self.game.ship.vx, 0)
        rock = Asteroid()
        self.game.rocks.append(rock)
        self.game.hit_ship(rock)
        self.assertFalse(self.game.active)
        self.assertEqual(self.game.lives, 0)
        self.assertFalse(self.game.rocks)

    def test_hit_and_draw(self):
        """Попадание удаляет ракету и камень, создаёт взрыв и очко."""
        import pygame
        self.game.start()
        rock = Asteroid()
        rock.x, rock.y = 100, 100
        rocket = Rocket(self.game.ship)
        rocket.x, rocket.y = 100, 100
        self.game.rocks = [rock]
        self.game.rockets = [rocket]
        self.game.update(0, pygame.key.get_pressed())
        self.assertEqual(self.game.score, 1)
        self.assertFalse(self.game.rocks)
        self.assertFalse(self.game.rockets)
        self.assertEqual(len(self.game.explosions), 1)
        self.game.draw(True)
        self.game.active = False
        self.game.draw()


if __name__ == '__main__':
    unittest.main()
