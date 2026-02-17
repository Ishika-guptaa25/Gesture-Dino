import pygame
import cv2
import numpy as np
from config import *
from dino import Dino
from obstacles import ObstacleManager
from gesture_controller import GestureController


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Gesture Dino Game 🦕")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 22)

        self.dino = Dino()
        self.obstacles = ObstacleManager()
        self.gesture_controller = GestureController()

        self.score = 0
        self.high_score = 0
        self.game_speed = GAME_SPEED_START
        self.running = True
        self.game_over = False

    def _draw_background(self):
        """Draw simple clean background"""
        # Sky
        self.screen.fill(SKY_BLUE)

        # Ground
        ground_y = GROUND_LEVEL + 60
        pygame.draw.rect(self.screen, GROUND_BROWN,
                         (0, ground_y, SCREEN_WIDTH, SCREEN_HEIGHT - ground_y))
        pygame.draw.line(self.screen, BLACK,
                         (0, ground_y), (SCREEN_WIDTH, ground_y), 2)

    def _draw_camera_feed(self):
        """Draw camera feed in top right corner"""
        camera_frame = self.gesture_controller.get_camera_frame()
        if camera_frame is not None:
            # Resize frame
            camera_width = 200
            camera_height = 150
            frame_resized = cv2.resize(camera_frame, (camera_width, camera_height))

            # Convert BGR to RGB for pygame
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(np.rot90(frame_rgb))

            # Position in top right corner
            camera_x = SCREEN_WIDTH - camera_width - 10
            camera_y = 10

            # Draw border
            pygame.draw.rect(self.screen, BLACK,
                             (camera_x - 2, camera_y - 2, camera_width + 4, camera_height + 4), 3)

            # Draw camera feed
            self.screen.blit(frame_surface, (camera_x, camera_y))

    def _draw_hud(self):
        """Draw score and instructions"""
        # Score
        score_text = self.font_medium.render(f"Score: {int(self.score)}", True, BLACK)
        self.screen.blit(score_text, (20, 20))

        # High Score
        high_score_text = self.font_small.render(f"Best: {int(self.high_score)}", True, BLACK)
        self.screen.blit(high_score_text, (20, 55))

        # Instructions
        instructions = self.font_small.render("PINCH fingers to JUMP!", True, BLACK)
        self.screen.blit(instructions, (20, SCREEN_HEIGHT - 40))

    def _draw_game_over_screen(self):
        """Draw game over overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Game Over text
        game_over_text = self.font_large.render("GAME OVER!", True, RED)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        self.screen.blit(game_over_text, text_rect)

        # Score
        score_text = self.font_medium.render(f"Score: {int(self.score)}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(score_text, score_rect)

        # High Score
        if self.score >= self.high_score:
            new_high = self.font_medium.render("NEW HIGH SCORE!", True, YELLOW)
            new_high_rect = new_high.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
            self.screen.blit(new_high, new_high_rect)

        # Restart instruction
        restart_text = self.font_small.render("PINCH or press SPACE to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(restart_text, restart_rect)

    def reset_game(self):
        """Reset game state"""
        self.dino = Dino()
        self.obstacles.reset()
        if self.score > self.high_score:
            self.high_score = self.score
        self.score = 0
        self.game_speed = GAME_SPEED_START
        self.game_over = False

    def handle_events(self):
        """Handle keyboard and gesture input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_SPACE:
                    if self.game_over:
                        self.reset_game()
                    else:
                        self.dino.jump()

        # Gesture control - check pinch
        if self.gesture_controller.should_jump():
            if self.game_over:
                self.reset_game()
            else:
                self.dino.jump()

    def update(self):
        """Update game state"""
        if self.game_over:
            return

        # Update game objects
        self.dino.update()
        self.obstacles.update(self.game_speed)

        # Check collision
        if self.obstacles.check_collision(self.dino.get_rect()):
            self.game_over = True

        # Update score and speed
        self.score += 0.1
        self.game_speed = GAME_SPEED_START + (self.score * GAME_SPEED_INCREMENT)

    def draw(self):
        """Draw everything"""
        self._draw_background()
        self.obstacles.draw(self.screen)
        self.dino.draw(self.screen)
        self._draw_camera_feed()  # Camera feed in same window!
        self._draw_hud()

        if self.game_over:
            self._draw_game_over_screen()

        pygame.display.flip()

    def run(self):
        """Main game loop"""
        print("🦕 Game shuru ho gaya!")
        print("✋ Pinch karo jump karne ke liye!")

        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.gesture_controller.cleanup()
        pygame.quit()
        print("\n👋 Bye!")