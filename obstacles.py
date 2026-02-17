import pygame
import random
from config import GROUND, WIDTH


# ═══════════════════════════════════════════════════════════
#   CACTUS
# ═══════════════════════════════════════════════════════════
class Cactus:
    VARIANTS = [
        {"stems": 1, "w": 22, "h": 55},
        {"stems": 2, "w": 44, "h": 50},
        {"stems": 3, "w": 60, "h": 58},
    ]

    def __init__(self, x):
        v = random.choice(self.VARIANTS)
        self.x      = x
        self.w      = v["w"]
        self.h      = v["h"]
        self.stems  = v["stems"]
        self.y_base = GROUND          # feet of cactus

    def update(self, speed):
        self.x -= speed

    def draw(self, screen, color):
        bx = self.x
        stem_w   = 18
        stem_gap = 22

        for i in range(self.stems):
            sx = bx + i * stem_gap
            sy = self.y_base - self.h

            # Main stem
            pygame.draw.rect(screen, color,
                             (sx, sy, stem_w, self.h),
                             border_radius=4)

            # Arms (only if tall enough)
            if self.h > 44:
                arm_y = sy + 14
                # left arm
                pygame.draw.rect(screen, color,
                                 (sx - 12, arm_y, 14, 8), border_radius=3)
                pygame.draw.rect(screen, color,
                                 (sx - 12, arm_y - 14, 8, 16), border_radius=3)
                # right arm
                pygame.draw.rect(screen, color,
                                 (sx + stem_w - 2, arm_y + 6, 14, 8), border_radius=3)
                pygame.draw.rect(screen, color,
                                 (sx + stem_w + 4, arm_y - 10, 8, 18), border_radius=3)

    def get_rect(self):
        return pygame.Rect(self.x + 2, self.y_base - self.h + 2,
                           self.w - 4, self.h - 4)

    def off_screen(self):
        return self.x < -(self.w + 20)


# ═══════════════════════════════════════════════════════════
#   BIRD  (must duck to avoid)
# ═══════════════════════════════════════════════════════════
class Bird:
    HEIGHTS = [GROUND - 80, GROUND - 130]   # two possible fly heights

    def __init__(self, x):
        self.x     = x
        self.y     = random.choice(self.HEIGHTS)
        self.w     = 40
        self.h     = 24
        self._flap = 0

    def update(self, speed):
        self.x   -= speed
        self._flap += 1

    def draw(self, screen, color):
        cx = self.x + self.w // 2
        cy = self.y + self.h // 2
        phase = (self._flap // 8) % 2

        # Body
        pygame.draw.ellipse(screen, color,
                            (self.x + 8, cy - 7, 26, 14))

        # Wings
        if phase == 0:
            wing_pts = [
                (cx - 6, cy - 4),
                (cx - 18, cy - 18),
                (cx + 2,  cy - 4),
            ]
        else:
            wing_pts = [
                (cx - 6, cy + 2),
                (cx - 18, cy + 14),
                (cx + 2,  cy + 2),
            ]
        pygame.draw.polygon(screen, color, wing_pts)

        # Beak
        pygame.draw.polygon(screen, color, [
            (self.x + self.w - 2, cy - 3),
            (self.x + self.w + 8, cy),
            (self.x + self.w - 2, cy + 3),
        ])

        # Eye
        pygame.draw.circle(screen, (255,255,255),
                           (self.x + self.w - 6, cy - 3), 4)
        pygame.draw.circle(screen, color,
                           (self.x + self.w - 5, cy - 3), 2)

    def get_rect(self):
        return pygame.Rect(self.x + 4, self.y + 2,
                           self.w - 6, self.h - 4)

    def off_screen(self):
        return self.x < -(self.w + 20)


# ═══════════════════════════════════════════════════════════
#   MANAGER
# ═══════════════════════════════════════════════════════════
class ObstacleManager:
    MIN_GAP = 270
    MAX_GAP = 480

    def __init__(self):
        self.obstacles = []
        self._next_x   = WIDTH + 200

    def update(self, speed):
        for o in self.obstacles:
            o.update(speed)

        self.obstacles = [o for o in self.obstacles if not o.off_screen()]

        # Spawn next obstacle
        if not self.obstacles or self.obstacles[-1].x < self._next_x - 200:
            if self.obstacles and self.obstacles[-1].x < WIDTH - 80:
                # choose cactus or bird (bird more rare early on)
                cls = Bird if random.random() < 0.30 else Cactus
                self.obstacles.append(cls(self._next_x))
                self._next_x = self.obstacles[-1].x + random.randint(
                    self.MIN_GAP, self.MAX_GAP)

        # seed first obstacle
        if not self.obstacles:
            self.obstacles.append(Cactus(WIDTH + 100))
            self._next_x = WIDTH + 100 + random.randint(self.MIN_GAP, self.MAX_GAP)

    def draw(self, screen, color):
        for o in self.obstacles:
            o.draw(screen, color)

    def check_collision(self, dino_rect):
        for o in self.obstacles:
            if dino_rect.colliderect(o.get_rect()):
                return True
        return False

    def has_incoming_bird(self):
        """True if there's a bird within 350 px ahead of the dino."""
        for o in self.obstacles:
            if isinstance(o, Bird) and 80 < o.x < 430:
                return True
        return False

    def reset(self):
        self.obstacles = []
        self._next_x   = WIDTH + 200