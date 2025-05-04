import pygame
import config

class Grass:
    def __init__(self, amount=config.DEFAULT_GRASS_AMOUNT):
        self.amount = amount
        self.max_amount = config.GRASS_MAX_AMOUNT
        self.growth_rate = config.GRASS_GROWTH_RATE

    def update(self):
        # Regenerate grass up to maximum amount
        self.amount = min(self.max_amount, self.amount + self.growth_rate)

    def draw(self, screen, pos, size):
        # Draw a green rectangle with transparency based on grass amount
        intensity = int(config.GRASS_COLOR_MAX * (self.amount / self.max_amount))
        color = (0, intensity, 0)
        pygame.draw.rect(screen, color, (pos[0], pos[1], size, size))