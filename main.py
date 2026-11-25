"""Игровой цикл, события, столкновения и переходы между состояниями."""
import math
import pygame
from settings import (
    WIDTH, HEIGHT, FPS, LIVES, TURN_SPEED, SHOT_DELAY, SPAWN_DELAY,
    SAFE_DISTANCE, BACKGROUND_SPEED, EXPLOSION_TIME, EXPLOSION_FRAMES,
    TILE_SIZE, BANNER_SIZE,
)
from entities import Ship, Rocket, Asteroid, Explosion, touches
from art import (
    make_background, make_layer, make_ship, make_explosions,
    wrap_blit, draw_asteroid,
)


class Game:
    """Управление жизненным циклом аркадной игры."""

    def __init__(self):
        """Создать окно, изображения, таймеры и начальную заставку."""
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Астероиды')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.large = pygame.font.Font(None, 52)
        self.background = make_background()
        self.layer = make_layer()
        self.ships = [make_ship(), make_ship(True)]
        self.sheet = make_explosions()
        self.banner = pygame.Rect(0, 0, *BANNER_SIZE)
        self.banner.center = WIDTH // 2, HEIGHT // 2
        self.offset = 0
        self.score, self.lives = 0, LIVES
        self.active = False
        self.ship = Ship()
        self.rocks, self.rockets, self.explosions = [], [], []
        self.spawn_timer = self.shot_timer = 0

    def start(self):
        """Начать новую игру, сбросив счёт и все игровые объекты."""
        self.score, self.lives = 0, LIVES
        self.ship = Ship()
        self.rocks, self.rockets, self.explosions = [], [], []
        self.spawn_timer = self.shot_timer = 0
        self.active = True

    def hit_ship(self, rock):
        """Убрать астероид и возродить корабль либо показать заставку."""
        self.rocks.remove(rock)
        self.explosions.append(Explosion(rock.x, rock.y))
        if self.lives == 0:
            self.active = False
            self.rocks.clear()
            self.rockets.clear()
            self.explosions.clear()
        else:
            self.lives -= 1
            self.ship = Ship()

    def update(self, dt, keys):
        """Обновить физику, таймеры и столкновения активной игры."""
        self.offset = (self.offset + BACKGROUND_SPEED * dt) % WIDTH
        if not self.active:
            return
        turn = (int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT]))
        self.ship.update(dt, keys[pygame.K_UP], turn * TURN_SPEED)
        self.shot_timer = max(0, self.shot_timer - dt)
        if keys[pygame.K_SPACE] and self.shot_timer <= 0:
            self.rockets.append(Rocket(self.ship))
            self.shot_timer = SHOT_DELAY
        self.spawn_timer += dt
        if self.spawn_timer >= SPAWN_DELAY:
            self.spawn_timer -= SPAWN_DELAY
            rock = Asteroid()
            dx = abs(rock.x - self.ship.x)
            dy = abs(rock.y - self.ship.y)
            distance = math.hypot(min(dx, WIDTH - dx),
                                  min(dy, HEIGHT - dy))
            if distance > SAFE_DISTANCE:
                self.rocks.append(rock)
        for rock in self.rocks:
            rock.move(dt)
        for rocket in self.rockets:
            rocket.update(dt)
        self.rockets = [r for r in self.rockets if r.life > 0]
        for explosion in self.explosions:
            explosion.age += dt
        self.explosions = [e for e in self.explosions
                           if e.age < EXPLOSION_TIME]
        for rocket in self.rockets[:]:
            for rock in self.rocks[:]:
                if touches(rocket, rock):
                    self.rocks.remove(rock)
                    self.rockets.remove(rocket)
                    self.explosions.append(Explosion(rock.x, rock.y))
                    self.score += 1
                    break
        for rock in self.rocks[:]:
            if touches(self.ship, rock):
                self.hit_ship(rock)
                break

    def draw(self, thrust=False):
        """Нарисовать фон, HUD и заставку либо игровые объекты."""
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.layer, (-self.offset, 0))
        self.screen.blit(self.layer, (WIDTH - self.offset, 0))
        if self.active:
            for rock in self.rocks:
                draw_asteroid(self.screen, rock)
            for rocket in self.rockets:
                image = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(image, (255, 230, 140), (5, 5), 4)
                wrap_blit(self.screen, image, rocket.x, rocket.y)
            image = pygame.transform.rotate(self.ships[bool(thrust)],
                                            -self.ship.angle)
            wrap_blit(self.screen, image, self.ship.x, self.ship.y)
            for explosion in self.explosions:
                frame = min(EXPLOSION_FRAMES - 1,
                            int(explosion.age / EXPLOSION_TIME
                                * EXPLOSION_FRAMES))
                tile = self.sheet.subsurface(
                    (frame * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE))
                wrap_blit(self.screen, tile, explosion.x, explosion.y)
        else:
            pygame.draw.rect(self.screen, (25, 45, 70), self.banner,
                             border_radius=16)
            pygame.draw.rect(self.screen, (100, 205, 235), self.banner,
                             width=2, border_radius=16)
            title = self.large.render('ASTEROIDS', True, (220, 245, 255))
            self.screen.blit(title, title.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 - 28)))
            prompt = self.font.render('Click here to start', True,
                                      (150, 215, 230))
            self.screen.blit(prompt, prompt.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 35)))
        hud = self.font.render(
            f'Lives: {self.lives}    Score: {self.score}',
            True, (235, 245, 255))
        self.screen.blit(hud, (20, 18))
        help_text = self.font.render(
            'Left / Right: turn    Up: thrust    Space: fire    Esc: exit',
            True, (150, 170, 190))
        self.screen.blit(help_text, (20, HEIGHT - 32))
        pygame.display.flip()

    def run(self):
        """Обрабатывать события и обновлять игру до закрытия окна."""
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif (event.type == pygame.KEYDOWN
                      and event.key == pygame.K_ESCAPE):
                    running = False
                elif (event.type == pygame.MOUSEBUTTONDOWN
                      and event.button == 1 and not self.active
                      and self.banner.collidepoint(event.pos)):
                    self.start()
            keys = pygame.key.get_pressed()
            self.update(dt, keys)
            self.draw(keys[pygame.K_UP])
        pygame.quit()


if __name__ == '__main__':
    Game().run()
