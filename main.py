"""
Gesture Dino Game
─────────────────
✋  Open hand   → JUMP
🤏  Pinch       → RUN  (normal)
🕹️  SPACE       → jump (keyboard)
⬇️  DOWN key    → duck (keyboard)
T   key         → toggle Light / Dark theme
ESC             → quit
"""

import pygame
import numpy as np
from config import WIDTH, HEIGHT, FPS, GROUND, THEMES
from dino       import Dino
from obstacles  import ObstacleManager
from gesture_controller import GestureController


# ── Camera overlay dims ──────────────────────────────────────
CAM_W, CAM_H = 200, 150
CAM_X = WIDTH - CAM_W - 12
CAM_Y = 10


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Dino Game 🦕")
        self.clock  = pygame.time.Clock()

        # Fonts  – monospace to look like Chrome dino HUD
        self.font_score = pygame.font.SysFont("monospace", 22, bold=True)
        self.font_ui    = pygame.font.SysFont("monospace", 15)
        self.font_big   = pygame.font.SysFont("monospace", 42, bold=True)
        self.font_med   = pygame.font.SysFont("monospace", 20, bold=True)

        self.theme_name  = "light"
        self.theme       = THEMES["light"]

        self.gesture     = GestureController()
        self.dino        = Dino()
        self.obstacles   = ObstacleManager()

        self.score       = 0.0
        self.hi_score    = 0.0
        self.speed       = 7.0
        self.game_over   = False
        self.running     = True

        # Edge-detection for open-hand jump (fire once per gesture)
        self._prev_open  = False

        # Clouds
        self.clouds = [{"x": 200 + i * 300, "y": 80 + (i % 3) * 40,
                         "r": 28 + i * 8}   for i in range(4)]

        # Ground dashes (animated)
        self.dash_offset = 0.0

    # ── theme ────────────────────────────────────────────────
    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.theme      = THEMES[self.theme_name]

    # ── helpers ──────────────────────────────────────────────
    def _c(self, key):
        return self.theme[key]

    # ── input ────────────────────────────────────────────────
    def handle_input(self):
        # ── gesture update (single call per frame) ──
        self.gesture.update()

        open_now = self.gesture.is_open()

        # Jump on rising edge of open hand
        if open_now and not self._prev_open:
            if self.game_over:
                self.reset()
            else:
                self.dino.jump()

        # Duck only when pinching (and game running)
        if not self.game_over:
            self.dino.duck(self.gesture.is_pinch())

        self._prev_open = open_now

        # ── keyboard ──
        keys = pygame.key.get_pressed()
        if not self.game_over and keys[pygame.K_DOWN]:
            self.dino.duck(True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_t:
                    self.toggle_theme()

                if event.key == pygame.K_SPACE:
                    if self.game_over:
                        self.reset()
                    else:
                        self.dino.jump()

    # ── update ───────────────────────────────────────────────
    def update(self):
        if self.game_over:
            return

        self.dino.update()
        self.obstacles.update(self.speed)

        if self.obstacles.check_collision(self.dino.get_rect()):
            self.game_over = True
            self.hi_score  = max(self.hi_score, self.score)
            return

        self.score      += 0.12
        self.speed       = 7.0 + self.score * 0.007
        self.dash_offset = (self.dash_offset + self.speed) % 60

        # Scroll clouds
        for cl in self.clouds:
            cl["x"] -= 0.6
            if cl["x"] < -80:
                cl["x"] = WIDTH + 60

    # ── draw ─────────────────────────────────────────────────
    def draw(self):
        c = self.theme

        # Background
        self.screen.fill(c["bg"])

        # Clouds
        for cl in self.clouds:
            self._draw_cloud(cl["x"], cl["y"], cl["r"])

        # Ground line + dashes
        ground_y = GROUND + 2
        pygame.draw.line(self.screen, c["ground"],
                         (0, ground_y), (WIDTH, ground_y), 2)
        for i in range(0, WIDTH + 60, 60):
            dx = int((i - self.dash_offset) % (WIDTH + 60))
            pygame.draw.line(self.screen, c["ground"],
                             (dx, ground_y + 6), (dx + 28, ground_y + 6), 1)

        # Game objects
        self.obstacles.draw(self.screen, c["obstacle"])
        self.dino.draw(self.screen, c["dino"])

        # HUD
        self._draw_hud()

        # Camera pip
        self._draw_camera()

        # Game over overlay
        if self.game_over:
            self._draw_gameover()

        pygame.display.flip()

    def _draw_cloud(self, x, y, r):
        c = self._c("cloud")
        pygame.draw.circle(self.screen, c, (int(x),       int(y)),     r)
        pygame.draw.circle(self.screen, c, (int(x + r),   int(y + 6)), r - 8)
        pygame.draw.circle(self.screen, c, (int(x - r + 4), int(y + 8)), r - 12)

    def _draw_hud(self):
        c = self._c("text")

        # Score  (right-aligned like Chrome Dino)
        score_str = f"HI {int(self.hi_score):05d}  {int(self.score):05d}"
        surf = self.font_score.render(score_str, True, c)
        self.screen.blit(surf, (WIDTH - surf.get_width() - CAM_W - 30, 14))

        # Gesture hint  (bottom-left)
        hints = [
            "✋ open  →  JUMP",
            "🤏 pinch →  duck",
            "T  →  theme",
        ]
        for i, h in enumerate(hints):
            s = self.font_ui.render(h, True, c)
            self.screen.blit(s, (10, HEIGHT - 68 + i * 18))

        # Bird warning  (subtle flash)
        if self.obstacles.has_incoming_bird():
            warn = self.font_ui.render("🐦 DUCK!", True, (200, 80, 80))
            self.screen.blit(warn, (self.dino.x + 60, self.dino.y - 90))

    def _draw_camera(self):
        frame = self.gesture.get_frame()
        if frame is None:
            return

        try:
            # Resize  (frame is HxWx3 RGB numpy)
            import cv2
            small = cv2.resize(frame, (CAM_W, CAM_H))
            # numpy → pygame surface  (need to transpose for surfarray)
            surf = pygame.surfarray.make_surface(np.transpose(small, (1, 0, 2)))

            # Rounded border
            border_col = self._c("ground")
            pygame.draw.rect(self.screen, border_col,
                             (CAM_X - 3, CAM_Y - 3, CAM_W + 6, CAM_H + 6),
                             border_radius=8)
            self.screen.blit(surf, (CAM_X, CAM_Y))

            # Label
            lbl = self.font_ui.render("camera", True, self._c("text"))
            self.screen.blit(lbl, (CAM_X + 4, CAM_Y + CAM_H + 4))
        except Exception:
            pass

    def _draw_gameover(self):
        # Semi-transparent panel
        panel = pygame.Surface((360, 180), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150) if self.theme_name == "dark"
                   else (255, 255, 255, 170))
        px = WIDTH // 2 - 180
        py = HEIGHT // 2 - 110
        self.screen.blit(panel, (px, py))

        tc = self._c("text")

        t1 = self.font_big.render("G A M E  O V E R", True, tc)
        self.screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, py + 18))

        t2 = self.font_med.render(f"Score  {int(self.score):05d}", True, tc)
        self.screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, py + 78))

        t3 = self.font_ui.render("open hand  /  SPACE  to restart", True, tc)
        self.screen.blit(t3, (WIDTH // 2 - t3.get_width() // 2, py + 118))

    # ── reset ────────────────────────────────────────────────
    def reset(self):
        self.dino      = Dino()
        self.obstacles.reset()
        self.score     = 0.0
        self.speed     = 7.0
        self.game_over = False
        self._prev_open = False

    # ── main loop ────────────────────────────────────────────
    def run(self):
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        self.gesture.close()
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()