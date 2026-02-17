import pygame
import numpy as np
import random
import math
import cv2

from config  import *
from dino    import Dino
from obstacles import ObstacleManager
from gesture_controller import GestureController


# ─────────────────────────────────────────────────────────────
#  Tiny helpers
# ─────────────────────────────────────────────────────────────
def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def surf_rounded(w, h, r, color, alpha=255):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))
    pygame.draw.rect(s, (*color, alpha), (0, 0, w, h), border_radius=r)
    return s


# ─────────────────────────────────────────────────────────────
#  THEME TOGGLE BUTTON
# ─────────────────────────────────────────────────────────────
class ThemeToggle:
    W, H  = 58, 30
    BTN_X = WIDTH  - CAM_W - 90
    BTN_Y = CAM_Y + CAM_H + 12

    def __init__(self):
        self.rect       = pygame.Rect(self.BTN_X, self.BTN_Y, self.W, self.H)
        self._anim_t    = 0.0     # 0 = light, 1 = dark
        self._target    = 0.0

    def set_theme(self, is_dark):
        self._target = 1.0 if is_dark else 0.0

    def update(self):
        # smooth slide animation
        self._anim_t += (self._target - self._anim_t) * 0.18

    def draw(self, screen, t):
        self.update()

        bg_c  = t["btn_bg"]
        knob_c = t["btn_knob"]
        W, H  = self.W, self.H
        x, y  = self.BTN_X, self.BTN_Y

        # Track
        pygame.draw.rect(screen, bg_c,
                         (x, y, W, H), border_radius=H // 2)

        # Knob slide
        knob_r  = H // 2 - 3
        knob_x0 = x + knob_r + 3
        knob_x1 = x + W - knob_r - 3
        kx      = int(knob_x0 + (knob_x1 - knob_x0) * self._anim_t)
        ky      = y + H // 2
        pygame.draw.circle(screen, knob_c, (kx, ky), knob_r)

        # ☀ / ☽  icons
        font = pygame.font.SysFont("segoeui", 14)
        sun  = font.render("☀", True, knob_c)
        moon = font.render("☽", True, knob_c)
        screen.blit(sun,  (x + 5,  y + H//2 - sun.get_height()//2))
        screen.blit(moon, (x + W - moon.get_width() - 5,
                            y + H//2 - moon.get_height()//2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ─────────────────────────────────────────────────────────────
#  STAR FIELD  (dark theme only)
# ─────────────────────────────────────────────────────────────
class Stars:
    def __init__(self, n=80):
        self.stars = [
            (random.randint(0, WIDTH),
             random.randint(0, GROUND_Y - 80),
             random.uniform(0.5, 2.0))
            for _ in range(n)
        ]

    def draw(self, screen, alpha):
        if alpha < 0.05:
            return
        for sx, sy, size in self.stars:
            r = max(1, int(size))
            a = int(alpha * 255)
            s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
            pygame.draw.circle(s, (220, 220, 255, a), (r+1, r+1), r)
            screen.blit(s, (sx - r, sy - r))


# ─────────────────────────────────────────────────────────────
#  GROUND  (animated dashes)
# ─────────────────────────────────────────────────────────────
class Ground:
    def __init__(self):
        self.offset   = 0.0
        self.pebbles  = [(random.randint(0, WIDTH),
                          random.randint(GROUND_Y + 12, GROUND_Y + 34),
                          random.randint(2, 5))
                         for _ in range(40)]

    def update(self, speed):
        self.offset = (self.offset + speed) % 60

    def draw(self, screen, t):
        gy = GROUND_Y

        # ── layered ground ──────────────────────────────
        # Grass strip
        pygame.draw.rect(screen, t["ground_top"],
                         (0, gy, WIDTH, 10))
        # Dirt
        pygame.draw.rect(screen, t["ground_mid"],
                         (0, gy + 10, WIDTH, 20))
        # Sub-soil
        pygame.draw.rect(screen, t["ground_bot"],
                         (0, gy + 30, WIDTH, HEIGHT - gy - 30))

        # Ground line
        pygame.draw.line(screen, t["ground_top"],
                         (0, gy), (WIDTH, gy), 2)

        # Animated dashes on grass
        dc = t["dash"]
        for i in range(-1, WIDTH // 60 + 2):
            dx = int(i * 60 - self.offset)
            pygame.draw.line(screen, dc,
                             (dx, gy + 3), (dx + 28, gy + 3), 2)

        # Pebbles (shift with speed)
        for idx, (px, py, pr) in enumerate(self.pebbles):
            nx = (px - int(self.offset) // 2) % (WIDTH + 20) - 10
            pygame.draw.circle(screen, t["ground_mid"], (nx, py), pr)


# ─────────────────────────────────────────────────────────────
#  CLOUDS
# ─────────────────────────────────────────────────────────────
class Clouds:
    def __init__(self):
        self.clouds = [
            {"x": random.randint(0, WIDTH),
             "y": random.randint(55, 180),
             "w": random.randint(70, 130),
             "h": random.randint(28, 46),
             "spd": random.uniform(0.4, 1.0)}
            for _ in range(7)
        ]

    def update(self, speed):
        for cl in self.clouds:
            cl["x"] -= cl["spd"] * (speed / 8)
            if cl["x"] < -(cl["w"] + 20):
                cl["x"]   = WIDTH + random.randint(20, 120)
                cl["y"]   = random.randint(55, 180)
                cl["w"]   = random.randint(70, 130)
                cl["spd"] = random.uniform(0.4, 1.0)

    def draw(self, screen, t):
        c  = t["cloud"]
        cs = t["cloud_shadow"]
        for cl in self.clouds:
            x, y, w, h = int(cl["x"]), int(cl["y"]), cl["w"], cl["h"]
            # shadow
            pygame.draw.ellipse(screen, cs,
                                (x + 4, y + 6, w, h // 2 + 4))
            # main puffs
            pygame.draw.ellipse(screen, c,
                                (x, y + h // 3, w, h * 2 // 3))
            pygame.draw.circle(screen, c,
                               (x + w // 3, y + h // 2), h // 2)
            pygame.draw.circle(screen, c,
                               (x + w * 2 // 3, y + h // 2), h // 2 - 2)
            pygame.draw.circle(screen, c,
                               (x + w // 2, y + h // 4 + 2), h // 2 + 2)


# ─────────────────────────────────────────────────────────────
#  MOUNTAINS  (parallax bg layer)
# ─────────────────────────────────────────────────────────────
class Mountains:
    def __init__(self):
        self._build()

    def _build(self):
        self.peaks1 = [(random.randint(0, WIDTH + 300), random.randint(120, 210))
                       for _ in range(12)]
        self.peaks2 = [(random.randint(0, WIDTH + 200), random.randint(160, 240))
                       for _ in range(14)]
        self.offset = 0.0

    def update(self, speed):
        self.offset += speed * 0.12

    def draw(self, screen, t):
        c1 = t["mountain1"]
        c2 = t["mountain2"]
        gy = GROUND_Y

        for layer, peaks, c in [(0, self.peaks2, c2), (1, self.peaks1, c1)]:
            off = self.offset * (0.4 if layer == 0 else 0.25)
            pts = []
            for px, py in peaks:
                x = (px - off) % (WIDTH + 360) - 180
                pts.append((x, py))

            # Sort by x, add ground corners
            pts.sort(key=lambda p: p[0])
            poly = [(0, gy)] + pts + [(WIDTH, gy)]
            if len(poly) >= 3:
                pygame.draw.polygon(screen, c, poly)


# ─────────────────────────────────────────────────────────────
#  SCORE HUD
# ─────────────────────────────────────────────────────────────
class ScoreHUD:
    def __init__(self):
        self.font_score = pygame.font.SysFont("couriernew", 22, bold=True)
        self.font_hi    = pygame.font.SysFont("couriernew", 14, bold=True)
        self._flash_t   = 0
        self._prev_100  = 0

    def notify_milestone(self):
        self._flash_t = 40

    def update(self, score):
        m = int(score) // 100
        if m > self._prev_100:
            self._prev_100 = m
            self.notify_milestone()
        if self._flash_t > 0:
            self._flash_t -= 1

    def draw(self, screen, t, score, hi_score):
        flash = self._flash_t > 0
        sc    = t["hi_text"] if flash else t["score_text"]
        hc    = t["hi_text"]

        # HI + score  (right side, Chrome-Dino style)
        hi_str = f"HI {int(hi_score):05d}"
        sc_str = f"{int(score):05d}"

        hi_surf = self.font_hi.render(hi_str, True, hc)
        sc_surf = self.font_score.render(sc_str, True, sc)

        rx = CAM_X - 20
        screen.blit(hi_surf, (rx - hi_surf.get_width() - 14, 18))
        screen.blit(sc_surf, (rx - sc_surf.get_width() - 14, 36))


# ─────────────────────────────────────────────────────────────
#  GESTURE HUD  (bottom left pill)
# ─────────────────────────────────────────────────────────────
class GestureHUD:
    GESTURES = [
        ("👆", "L-shape", "JUMP"),
        ("✊", "Fist",    "DUCK"),
        ("🤏", "Pinch",   "RUN"),
    ]

    def __init__(self):
        self.font = pygame.font.SysFont("segoeui", 15)

    def draw(self, screen, t, current_gesture):
        x, y = 14, HEIGHT - 78
        pad  = 10
        row_h = 22

        # Background pill
        bg_w = 220
        bg_h = len(self.GESTURES) * row_h + pad * 2
        panel = surf_rounded(bg_w, bg_h, 12,
                             t["panel_bg"], 200)
        screen.blit(panel, (x - pad, y - pad))

        for i, (emoji, name, action) in enumerate(self.GESTURES):
            ry   = y + i * row_h
            # Highlight active gesture
            g_map = {"jump": "JUMP", "duck": "DUCK", "run": "RUN"}
            active = g_map.get(current_gesture) == action

            col = (70, 180, 70) if active else t["hint_text"]

            s = self.font.render(f"{emoji}  {name:<10} → {action}", True, col)
            screen.blit(s, (x, ry))


# ─────────────────────────────────────────────────────────────
#  PARTICLE SYSTEM  (dust on jump/land, death flash)
# ─────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        self.x   = x + random.randint(-8, 8)
        self.y   = y + random.randint(-4, 4)
        self.vx  = random.uniform(-2.5, 2.5)
        self.vy  = random.uniform(-4.0, -0.5)
        self.life = random.randint(18, 32)
        self.r   = random.randint(2, 5)
        self.color = color

    def update(self):
        self.x   += self.vx
        self.y   += self.vy
        self.vy  += 0.25
        self.life -= 1

    def draw(self, screen):
        a = max(0, int(255 * self.life / 32))
        s = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, a), (self.r, self.r), self.r)
        screen.blit(s, (int(self.x) - self.r, int(self.y) - self.r))


# ─────────────────────────────────────────────────────────────
#  GAME OVER SCREEN
# ─────────────────────────────────────────────────────────────
class GameOverScreen:
    def __init__(self):
        self.font_big  = pygame.font.SysFont("couriernew", 36, bold=True)
        self.font_med  = pygame.font.SysFont("couriernew", 22, bold=True)
        self.font_sm   = pygame.font.SysFont("couriernew", 14)
        self._anim_t   = 0

    def reset(self):
        self._anim_t = 0

    def draw(self, screen, t, score, hi_score):
        self._anim_t = min(self._anim_t + 1, 30)
        alpha        = int(220 * self._anim_t / 30)

        # Panel
        pw, ph = 440, 210
        px = WIDTH // 2 - pw // 2
        py = GROUND_Y // 2 - ph // 2 - 20

        panel = surf_rounded(pw, ph, 20, t["panel_bg"], alpha)
        screen.blit(panel, (px, py))

        if self._anim_t < 10:
            return

        tc  = t["go_title"]
        sc  = t["go_sub"]
        hc  = t["hi_text"]

        # GAME OVER
        g1  = self.font_big.render("GAME  OVER", True, tc)
        screen.blit(g1, (WIDTH//2 - g1.get_width()//2, py + 22))

        # Divider
        pygame.draw.line(screen, sc,
                         (px + 30, py + 78), (px + pw - 30, py + 78), 1)

        # Score row
        sc_lbl = self.font_sm.render("SCORE", True, sc)
        sc_val = self.font_med.render(f"{int(score):05d}", True, tc)
        screen.blit(sc_lbl, (WIDTH//2 - 110, py + 92))
        screen.blit(sc_val, (WIDTH//2 - 110, py + 110))

        # HI row
        hi_lbl = self.font_sm.render("BEST", True, hc)
        hi_val = self.font_med.render(f"{int(hi_score):05d}", True, hc)
        screen.blit(hi_lbl, (WIDTH//2 + 20, py + 92))
        screen.blit(hi_val, (WIDTH//2 + 20, py + 110))

        # Restart hint
        hint = self.font_sm.render(
            "👆 L-shape  or  SPACE  to restart", True, sc)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, py + ph - 36))


# ─────────────────────────────────────────────────────────────
#  MAIN GAME
# ─────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Gesture Dino  🦕")
        self.clock  = pygame.time.Clock()

        # subsystems
        self.gesture   = GestureController()
        self.dino      = Dino()
        self.obstacles = ObstacleManager()
        self.ground    = Ground()
        self.clouds    = Clouds()
        self.mountains = Mountains()
        self.stars     = Stars()
        self.score_hud = ScoreHUD()
        self.gesture_hud = GestureHUD()
        self.go_screen = GameOverScreen()
        self.toggle    = ThemeToggle()

        # game state
        self.theme_name   = "light"
        self.theme        = THEMES["light"]
        self._dark_alpha  = 0.0     # 0=light, 1=dark (smooth blend)
        self.score        = 0.0
        self.hi_score     = 0.0
        self.speed        = SPEED_START
        self.game_over    = False
        self.running      = True
        self._particles   : list[Particle] = []
        self._prev_jump   = False
        self._prev_duck   = False
        self._on_ground_last = True

    # ── theme ─────────────────────────────────────────────────
    def _toggle_theme(self):
        if self.theme_name == "light":
            self.theme_name = "dark"
        else:
            self.theme_name = "light"
        self.theme = THEMES[self.theme_name]
        self.toggle.set_theme(self.theme_name == "dark")

    # ── gradient sky ──────────────────────────────────────────
    def _draw_sky(self):
        t   = self.theme
        top = t["sky_top"]
        bot = t["sky_bottom"]
        for y in range(GROUND_Y):
            frac = y / GROUND_Y
            col  = lerp_color(top, bot, frac)
            pygame.draw.line(self.screen, col, (0, y), (WIDTH, y))

    # ── sun / moon ────────────────────────────────────────────
    def _draw_sun(self):
        t = self.theme
        sx, sy = 90, 70
        # glow
        glow = surf_rounded(80, 80, 40, t["sun_glow"], 80)
        self.screen.blit(glow, (sx - 40, sy - 40))
        # body
        pygame.draw.circle(self.screen, t["sun"], (sx, sy), 26)

    # ── camera PiP ────────────────────────────────────────────
    def _draw_camera(self):
        frame = self.gesture.get_frame()
        if frame is None:
            return
        try:
            small = cv2.resize(frame, (CAM_W, CAM_H))
            surf  = pygame.surfarray.make_surface(
                        np.transpose(small, (1, 0, 2)))

            border = self.theme["ground_top"]
            # outer border / rounded effect
            pygame.draw.rect(self.screen, border,
                             (CAM_X - 3, CAM_Y - 3,
                              CAM_W + 6, CAM_H + 6),
                             border_radius=10)
            self.screen.blit(surf, (CAM_X, CAM_Y))

            # label
            font = pygame.font.SysFont("couriernew", 12)
            lbl  = font.render("GESTURE CAM", True, self.theme["hint_text"])
            self.screen.blit(lbl, (CAM_X, CAM_Y + CAM_H + 3))
        except Exception:
            pass

    # ── input ─────────────────────────────────────────────────
    def _handle_input(self):
        self.gesture.update()

        jump_now = self.gesture.is_jump()
        duck_now = self.gesture.is_duck()

        # Rising edge for jump
        if jump_now and not self._prev_jump:
            if self.game_over:
                self._restart()
            else:
                self.dino.jump()

        # Duck continuously while fist
        if not self.game_over:
            self.dino.set_duck(duck_now)

        self._prev_jump = jump_now
        self._prev_duck = duck_now

        # Keyboard
        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN] and not self.game_over:
            self.dino.set_duck(True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    if self.game_over:
                        self._restart()
                    else:
                        self.dino.jump()

            # Click toggle button
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.toggle.is_clicked(event.pos):
                    self._toggle_theme()

    # ── update ────────────────────────────────────────────────
    def _update(self):
        # Smooth dark alpha
        target_dark = 1.0 if self.theme_name == "dark" else 0.0
        self._dark_alpha += (target_dark - self._dark_alpha) * 0.06

        if self.game_over:
            return

        self.dino.update()
        self.obstacles.update(self.speed, self.score)
        self.ground.update(self.speed)
        self.clouds.update(self.speed)
        self.mountains.update(self.speed)

        # Particles: dust on landing
        on_ground = not self.dino.jumping
        if on_ground and not self._on_ground_last:
            for _ in range(10):
                self._particles.append(
                    Particle(self.dino.x + 22, GROUND_Y,
                             self.theme["ground_top"]))
        self._on_ground_last = on_ground

        # Update particles
        for p in self._particles:
            p.update()
        self._particles = [p for p in self._particles if p.life > 0]

        # Collision
        if self.obstacles.check_collision(self.dino.get_rect()):
            self.dino.kill()
            self.game_over = True
            self.hi_score  = max(self.hi_score, self.score)
            self.go_screen.reset()
            # Death particles
            for _ in range(20):
                self._particles.append(
                    Particle(self.dino.x + 22, self.dino.y - 30,
                             (220, 80, 80)))
            return

        # Score & speed
        self.score += 0.14
        self.speed  = min(SPEED_MAX,
                          SPEED_START + self.score * SPEED_INC)
        self.score_hud.update(self.score)

    # ── draw ──────────────────────────────────────────────────
    def _draw(self):
        t = self.theme

        self._draw_sky()
        self.stars.draw(self.screen, self._dark_alpha)
        self._draw_sun()
        self.mountains.draw(self.screen, t)
        self.clouds.draw(self.screen, t)
        self.ground.draw(self.screen, t)

        self.obstacles.draw(self.screen, t)
        self.dino.draw(self.screen, t)

        # Particles
        for p in self._particles:
            p.draw(self.screen)

        # Bird warning
        if self.obstacles.has_incoming_bird(self.dino.x):
            font = pygame.font.SysFont("segoeui", 16)
            warn = font.render("⬇ DUCK!", True, (220, 80, 80))
            self.screen.blit(warn,
                             (self.dino.x + 55, self.dino.y - 80))

        # HUD elements
        self.score_hud.draw(self.screen, t, self.score, self.hi_score)
        # self.gesture_hud.draw(self.screen, t, self.gesture.gesture)
        self._draw_camera()
        self.toggle.draw(self.screen, t)

        # Speed bar (tiny strip above ground)
        speed_pct = (self.speed - SPEED_START) / (SPEED_MAX - SPEED_START)
        bar_w     = int(WIDTH * speed_pct)
        if bar_w > 0:
            bar_surf = pygame.Surface((bar_w, 3), pygame.SRCALPHA)
            bar_surf.fill((*t["ground_top"], 160))
            self.screen.blit(bar_surf, (0, GROUND_Y - 5))

        if self.game_over:
            self.go_screen.draw(self.screen, t, self.score, self.hi_score)

        pygame.display.flip()

    # ── restart ───────────────────────────────────────────────
    def _restart(self):
        self.dino      = Dino()
        self.obstacles.reset()
        self.score     = 0.0
        self.speed     = SPEED_START
        self.game_over = False
        self._particles.clear()
        self._prev_jump   = False
        self._on_ground_last = True

    # ── run ───────────────────────────────────────────────────
    def run(self):
        while self.running:
            self._handle_input()
            self._update()
            self._draw()
            self.clock.tick(FPS)

        self.gesture.close()
        pygame.quit()


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    g = Game()
    g.run()