import pygame
from config import GROUND, GRAVITY, JUMP_VEL, DUCK_HEIGHT


class Dino:
    STAND_H = 54
    STAND_W = 44
    DUCK_W  = 58
    DUCK_H  = DUCK_HEIGHT

    def __init__(self):
        self.reset()

    def reset(self):
        self.x      = 90
        self.y      = GROUND
        self.vel_y  = 0
        self.jumping = False
        self.ducking = False
        self.dead    = False
        self._step   = 0          # animation tick

    # ── actions ──────────────────────────────────────────
    def jump(self):
        if not self.jumping and not self.dead:
            self.vel_y   = JUMP_VEL
            self.jumping = True
            self.ducking = False

    def duck(self, active: bool):
        if not self.jumping and not self.dead:
            self.ducking = active

    # ── per-frame update ─────────────────────────────────
    def update(self):
        if self.dead:
            return
        self._step += 1

        # Physics
        self.vel_y += GRAVITY
        self.y     += self.vel_y

        if self.y >= GROUND:
            self.y      = GROUND
            self.vel_y  = 0
            self.jumping = False

    # ── geometry ─────────────────────────────────────────
    @property
    def w(self):  return self.DUCK_W if self.ducking else self.STAND_W
    @property
    def h(self):  return self.DUCK_H if self.ducking else self.STAND_H

    def get_rect(self):
        return pygame.Rect(self.x + 4, self.y - self.h + 4,
                           self.w - 8, self.h - 8)

    # ── drawing ──────────────────────────────────────────
    def draw(self, screen, color):
        if self.ducking:
            self._draw_duck(screen, color)
        else:
            self._draw_stand(screen, color)

    def _draw_stand(self, screen, c):
        x, y = self.x, self.y
        h = self.STAND_H
        w = self.STAND_W

        # ── body ──
        pygame.draw.rect(screen, c, (x + 6, y - h + 14, w - 8, h - 18), border_radius=4)

        # ── neck + head ──
        pygame.draw.rect(screen, c, (x + 14, y - h,      16, 22), border_radius=5)

        # ── eye white ──
        pygame.draw.circle(screen, (255, 255, 255), (x + 24, y - h + 7), 6)
        # ── pupil ──
        pygame.draw.circle(screen, c,               (x + 25, y - h + 7), 3)

        # ── mouth line ──
        pygame.draw.line(screen, c, (x + 18, y - h + 17), (x + 28, y - h + 17), 2)

        # ── tail ──
        tail = [
            (x + 6, y - h + 18),
            (x - 5, y - h + 22),
            (x - 2, y - h + 30),
            (x + 6, y - h + 26),
        ]
        pygame.draw.polygon(screen, c, tail)

        # ── arm ──
        pygame.draw.rect(screen, c, (x + 4, y - h + 26, 14, 8), border_radius=3)

        # ── legs (animated) ──
        phase = (self._step // 8) % 2
        if not self.jumping:
            if phase == 0:
                pygame.draw.rect(screen, c, (x + 8,  y - 18, 10, 18), border_radius=3)
                pygame.draw.rect(screen, c, (x + 22, y - 10, 10, 10), border_radius=3)
            else:
                pygame.draw.rect(screen, c, (x + 8,  y - 10, 10, 10), border_radius=3)
                pygame.draw.rect(screen, c, (x + 22, y - 18, 10, 18), border_radius=3)
        else:
            # Both legs bent upward while airborne
            pygame.draw.rect(screen, c, (x + 8,  y - 14, 10, 14), border_radius=3)
            pygame.draw.rect(screen, c, (x + 22, y - 14, 10, 14), border_radius=3)

    def _draw_duck(self, screen, c):
        x, y = self.x, self.y
        w = self.DUCK_W
        h = self.DUCK_H

        # Low flat body
        pygame.draw.rect(screen, c, (x + 4, y - h + 4, w - 8, h - 8), border_radius=6)

        # Small head to the right
        pygame.draw.rect(screen, c, (x + w - 20, y - h - 4, 20, 18), border_radius=5)
        # Eye
        pygame.draw.circle(screen, (255,255,255), (x + w - 9, y - h + 3), 5)
        pygame.draw.circle(screen, c,             (x + w - 8, y - h + 3), 2)

        # Stubby legs
        phase = (self._step // 8) % 2
        if phase == 0:
            pygame.draw.rect(screen, c, (x + 10, y - 12, 10, 12), border_radius=3)
            pygame.draw.rect(screen, c, (x + 28, y - 7,  10, 7),  border_radius=3)
        else:
            pygame.draw.rect(screen, c, (x + 10, y - 7,  10, 7),  border_radius=3)
            pygame.draw.rect(screen, c, (x + 28, y - 12, 10, 12), border_radius=3)