###############################################
# Imports
###############################################

from __future__ import annotations
import pygame
import config

################################################
# Grass Class
################################################

class Grass:
    """Represents a grass chunk in the ecosystem.
    
    Grass serves as food for prey animals and regenerates over time
    up to a maximum amount.
    
    Attributes:
        amount: Current amount of grass in this chunk.
        max_amount: Maximum grass capacity for this chunk.
        growth_rate: Rate at which grass regenerates per tick.
    """
    
    def __init__(self, amount: float = config.DEFAULT_GRASS_AMOUNT) -> None:
        """Initialize a grass chunk with the given amount.
        
        Args:
            amount: Initial grass amount (defaults to config value).
        """
        self.amount = amount
        self.max_amount = config.GRASS_MAX_AMOUNT
        self.growth_rate = config.GRASS_GROWTH_RATE

    def update(self) -> None:
        """Update the grass chunk, regenerating grass up to the maximum."""
        # Regenerate grass up to maximum amount
        self.amount = min(self.max_amount, self.amount + self.growth_rate)

    def draw(self, screen: pygame.Surface, pos: tuple[int, int], size: int) -> None:
        """Draw the grass chunk as a green rectangle.
        
        The green intensity varies based on the current grass amount
        relative to the maximum.
        
        Args:
            screen: The pygame surface to draw on.
            pos: The (x, y) position of the top-left corner.
            size: The size of the grass chunk in pixels.
        """
        # Draw a green rectangle with transparency based on grass amount
        intensity = int(config.GRASS_COLOR_MAX * (self.amount / self.max_amount))
        color = (0, intensity, 0)
        pygame.draw.rect(screen, color, (pos[0], pos[1], size, size))