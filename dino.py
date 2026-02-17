"""
Dino sprite — drawn with pygame primitives, pixel-art style.
Matches the real Chrome Dino proportions.
"""
import pygame
from config import GROUND_Y, GRAVITY, JUMP_VEL


class Dino:
    # ── pixel sizes ──────────────────────────────────────────
    STAND_W, STAND_H = 44, 58
    DUCK_W,  DUCK_H  = 62, 32

    def __init__(self):
        self._step = 0
        self.reset()

    def reset(self):
        self.x        = 85
        self.y        = GROUND_Y          # feet position
        self.vel_y    = 0.0
        self.jumping  = False
        self.ducking  = False
        self.dead     = False
        self._blink   = 0
        self._step    = 0
        self._death_frame = 0

    # ── actions ──────────────────────────────────────────────
    def jump(self):
        if not self.jumping and not self.dead:
            self.vel_y  = JUMP_VEL
            self.jumping = True
            self.ducking = False

    def set_duck(self, active: bool):
        if not self.jumping and not self.dead:
            self.ducking = active

    def kill(self):
        self.dead = True

    # ── properties ───────────────────────────────────────────
    @property
    def w(self):
        return self.DUCK_W if self.ducking else self.STAND_W
    @property
    def h(self):
        return self.DUCK_H if self.ducking else self.STAND_H

    def get_rect(self):
        margin = 6
        return pygame.Rect(self.x + margin, self.y - self.h + margin,
                           self.w - margin*2, self.h - margin*2)

    # ── update ───────────────────────────────────────────────
    def update(self):
        if self.dead:
            self._death_frame += 1
            return

        self._step += 1
        self._blink = (self._blink + 1) % 90   # blink cycle

        # Physics
        self.vel_y += GRAVITY
        self.y     += self.vel_y
        if self.y >= GROUND_Y:
            self.y      = GROUND_Y
            self.vel_y  = 0.0
            self.jumping = False

    # ── master draw dispatcher ───────────────────────────────
    def draw(self, screen, t):
        if self.ducking:
            self._draw_duck(screen, t)
        else:
            self._draw_stand(screen, t)

        if self.dead:
            self._draw_dead_x(screen, t)

    # ── STAND / RUN / JUMP ───────────────────────────────────
    def _draw_stand(self, screen, t):
        c       = t["dino"]
        c_eye   = t["dino_eye"]
        c_pupil = t["dino_pupil"]
        x       = self.x
        fy      = self.y        # feet y
        # origin: bottom-left of dino = (x, fy)
        # all coords relative to (x, fy)

        def R(rx, ry, rw, rh, radius=3):
            pygame.draw.rect(screen, c,
                             (x + rx, fy + ry, rw, rh),
                             border_radius=radius)

        # ── tail ──────────────────────────────────────────
        tail = [
            (x + 0,  fy - 28),
            (x - 12, fy - 20),
            (x - 8,  fy - 10),
            (x + 4,  fy - 14),
        ]
        pygame.draw.polygon(screen, c, tail)

        # ── body ──────────────────────────────────────────
        R(4, -44, 28, 28, 4)        # main torso

        # ── neck ──────────────────────────────────────────
        R(20, -54, 14, 16, 3)

        # ── head ──────────────────────────────────────────
        R(18, -58, 22, 18, 5)

        # ── jaw / snout ───────────────────────────────────
        R(26, -44, 16, 8, 3)

        # ── eye white ─────────────────────────────────────
        blink = self._blink > 82
        if blink:
            pygame.draw.line(screen, c_pupil,
                             (x + 33, fy - 52), (x + 39, fy - 52), 3)
        else:
            pygame.draw.circle(screen, c_eye,   (x+36, fy-53), 7)
            pygame.draw.circle(screen, c_pupil, (x+37, fy-52), 4)

        # ── arm stub ──────────────────────────────────────
        R(14, -32, 14, 7, 3)

        # ── legs ──────────────────────────────────────────
        phase = (self._step // 7) % 2
        if self.jumping:
            # Both legs together, bent back
            R(6,  -18, 10, 18, 3)
            R(20, -18, 10, 18, 3)
        elif phase == 0:
            R(6,  -20, 10, 20, 3)
            R(20, -12, 10, 12, 3)
        else:
            R(6,  -12, 10, 12, 3)
            R(20, -20, 10, 20, 3)

    # ── DUCK ─────────────────────────────────────────────────
    def _draw_duck(self, screen, t):
        c       = t["dino"]
        c_eye   = t["dino_eye"]
        c_pupil = t["dino_pupil"]
        x       = self.x
        fy      = self.y

        def R(rx, ry, rw, rh, radius=3):
            pygame.draw.rect(screen, c,
                             (x + rx, fy + ry, rw, rh),
                             border_radius=radius)

        # Low flat body
        R(0, -26, 44, 22, 5)

        # Tail
        tail = [(x, fy-18), (x-12, fy-12), (x-6, fy-4), (x+4, fy-8)]
        pygame.draw.polygon(screen, c, tail)

        # Neck + head poking forward
        R(36, -30, 14, 12, 4)
        R(44, -28, 16, 16, 5)

        # Snout
        R(52, -18, 12, 8, 3)

        # Eye
        blink = self._blink > 82
        if blink:
            pygame.draw.line(screen, c_pupil,
                             (x+54, fy-26), (x+58, fy-26), 3)
        else:
            pygame.draw.circle(screen, c_eye,   (x+56, fy-25), 6)
            pygame.draw.circle(screen, c_pupil, (x+57, fy-24), 3)

        # Short legs
        phase = (self._step // 7) % 2
        if phase == 0:
            R(8,  -8, 10, 8, 3)
            R(26, -5, 10, 5, 3)
        else:
            R(8,  -5, 10, 5, 3)
            R(26, -8, 10, 8, 3)

    # ── DEAD X eyes ──────────────────────────────────────────
    def _draw_dead_x(self, screen, t):
        c = t["dino"]
        x = self.x
        fy = self.y
        ex, ey = x + 36, fy - 53
        size = 6
        pygame.draw.line(screen, (220, 60, 60),
                         (ex-size, ey-size), (ex+size, ey+size), 4)
        pygame.draw.line(screen, (220, 60, 60),
                         (ex+size, ey-size), (ex-size, ey+size), 4)