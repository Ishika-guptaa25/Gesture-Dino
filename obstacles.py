"""
Obstacles:
  Cactus  – 6 variants (small/tall × 1/2/3 stems)
  Pterodactyl – flies at 2 heights, must duck
"""
import pygame
import random
from config import GROUND_Y, WIDTH


# ═══════════════════════════════════════════════════════════════
#  CACTUS
# ═══════════════════════════════════════════════════════════════
class Cactus:
    # (stem_count, stem_h, has_arms)
    VARIANTS = [
        (1, 50, True),
        (1, 66, True),
        (2, 50, True),
        (2, 60, True),
        (3, 50, False),
        (3, 60, True),
    ]

    STEM_W = 20

    def __init__(self, x):
        stems, sh, arms = random.choice(self.VARIANTS)
        self.x         = x
        self.stems     = stems
        self.stem_h    = sh
        self.has_arms  = arms
        self.w         = stems * (self.STEM_W + 6) - 6
        self.h         = sh

    # ── per-frame ─────────────────────────────────────────
    def update(self, speed):
        self.x -= speed

    def off_screen(self):
        return self.x < -(self.w + 30)

    def get_rect(self):
        # tight collision box
        return pygame.Rect(self.x + 2, GROUND_Y - self.h + 2,
                           self.w - 4, self.h - 4)

    # ── draw ──────────────────────────────────────────────
    def draw(self, screen, t):
        c  = t["cactus"]
        cd = t["cactus_dark"]
        sw = self.STEM_W

        for i in range(self.stems):
            sx = self.x + i * (sw + 6)
            sy = GROUND_Y - self.stem_h

            # Main stem
            pygame.draw.rect(screen, c,
                             (sx, sy, sw, self.stem_h), border_radius=4)
            # Shade strip
            pygame.draw.rect(screen, cd,
                             (sx + sw - 6, sy, 6, self.stem_h), border_radius=2)

            # Rounded top
            pygame.draw.ellipse(screen, c,
                                (sx - 1, sy - 4, sw + 2, 12))

            if self.has_arms and self.stem_h >= 50:
                arm_y   = sy + 14
                arm_h   = 12
                arm_len = 18

                # ── left arm ──
                pygame.draw.rect(screen, c,
                                 (sx - arm_len, arm_y + 4, arm_len, arm_h - 2),
                                 border_radius=3)
                pygame.draw.rect(screen, c,
                                 (sx - arm_len, arm_y - 14, arm_h, 20),
                                 border_radius=3)
                # shade
                pygame.draw.rect(screen, cd,
                                 (sx - arm_len, arm_y + 4, arm_len, 4),
                                 border_radius=2)

                # ── right arm ──
                pygame.draw.rect(screen, c,
                                 (sx + sw, arm_y + 8, arm_len, arm_h - 2),
                                 border_radius=3)
                pygame.draw.rect(screen, c,
                                 (sx + sw + arm_len - arm_h, arm_y - 10, arm_h, 22),
                                 border_radius=3)
                pygame.draw.rect(screen, cd,
                                 (sx + sw, arm_y + 8, arm_len, 4),
                                 border_radius=2)


# ═══════════════════════════════════════════════════════════════
#  PTERODACTYL  (bird)
# ═══════════════════════════════════════════════════════════════
class Pterodactyl:
    # fly heights: low (head-level), mid (jump-zone)
    FLY_HEIGHTS = [GROUND_Y - 78, GROUND_Y - 130]

    def __init__(self, x):
        self.x     = x
        self.y     = random.choice(self.FLY_HEIGHTS)  # top of bird
        self.w     = 48
        self.h     = 34
        self._flap = 0

    def update(self, speed):
        self.x    -= speed
        self._flap = (self._flap + 1) % 16

    def off_screen(self):
        return self.x < -(self.w + 30)

    def get_rect(self):
        return pygame.Rect(self.x + 6, self.y + 4,
                           self.w - 10, self.h - 8)

    def draw(self, screen, t):
        c  = t["bird"]
        cw = t["bird_wing"]
        x, y = self.x, self.y
        cx = x + self.w // 2
        cy = y + self.h // 2

        # ── body ──────────────────────────────────────
        pygame.draw.ellipse(screen, c,
                            (x + 12, cy - 8, 26, 16))

        # ── head ──────────────────────────────────────
        pygame.draw.circle(screen, c, (x + self.w - 2, cy - 6), 9)

        # ── beak ──────────────────────────────────────
        beak = [
            (x + self.w + 7,  cy - 7),
            (x + self.w + 20, cy - 4),
            (x + self.w + 7,  cy - 1),
        ]
        pygame.draw.polygon(screen, c, beak)

        # ── eye ───────────────────────────────────────
        pygame.draw.circle(screen, (255,255,255),
                           (x + self.w - 1, cy - 8), 4)
        pygame.draw.circle(screen, c,
                           (x + self.w,    cy - 8), 2)

        # ── wings (flapping) ──────────────────────────
        wing_phase = self._flap < 8       # up or down

        if wing_phase:
            # wings up
            left_wing = [
                (cx - 4,  cy - 6),
                (cx - 24, cy - 26),
                (cx + 2,  cy - 8),
            ]
            right_wing = [
                (cx + 4,  cy - 6),
                (cx + 18, cy - 24),
                (cx + 10, cy - 4),
            ]
        else:
            # wings down
            left_wing = [
                (cx - 4,  cy + 2),
                (cx - 24, cy + 18),
                (cx + 2,  cy + 4),
            ]
            right_wing = [
                (cx + 4,  cy + 2),
                (cx + 18, cy + 16),
                (cx + 10, cy + 6),
            ]

        pygame.draw.polygon(screen, cw, left_wing)
        pygame.draw.polygon(screen, cw, right_wing)

        # ── tail ──────────────────────────────────────
        tail = [
            (x + 14, cy - 2),
            (x,      cy - 10),
            (x + 2,  cy + 4),
        ]
        pygame.draw.polygon(screen, c, tail)


# ═══════════════════════════════════════════════════════════════
#  OBSTACLE MANAGER
# ═══════════════════════════════════════════════════════════════
class ObstacleManager:
    MIN_GAP = 280
    MAX_GAP = 520

    def __init__(self):
        self.reset()

    def reset(self):
        self.obstacles  = []
        self._next_x    = WIDTH + 180
        self._score_ref = 0.0      # used to gate pterodactyl appearance

    def update(self, speed, score):
        self._score_ref = score

        for o in self.obstacles:
            o.update(speed)

        self.obstacles = [o for o in self.obstacles if not o.off_screen()]

        # spawn
        spawn_due = (not self.obstacles or
                     self.obstacles[-1].x < self._next_x - 60)
        if spawn_due:
            # only spawn pterodactyl after score 300
            use_bird = (score > 300 and random.random() < 0.28)
            cls      = Pterodactyl if use_bird else Cactus
            self.obstacles.append(cls(self._next_x))
            gap = random.randint(self.MIN_GAP, self.MAX_GAP)
            self._next_x = self._next_x + gap

        # seed very first obstacle
        if not self.obstacles:
            self.obstacles.append(Cactus(WIDTH + 120))
            self._next_x = WIDTH + 120 + random.randint(self.MIN_GAP, self.MAX_GAP)

    def draw(self, screen, t):
        for o in self.obstacles:
            o.draw(screen, t)

    def check_collision(self, dino_rect):
        for o in self.obstacles:
            if dino_rect.colliderect(o.get_rect()):
                return True
        return False

    def has_incoming_bird(self, dino_x=85):
        for o in self.obstacles:
            if isinstance(o, Pterodactyl) and dino_x < o.x < dino_x + 420:
                return True
        return False