###############################################
# Imports
###############################################

from __future__ import annotations
import pygame
import config

# Pre-compute color lookup table for grass intensity (0-max_amount mapped to green intensity)
# This avoids division and int conversion every frame
GRASS_COLOR_LUT: list[tuple[int, int, int]] = []

def init_grass_color_lut() -> None:
    """Initialize the grass color lookup table for fast drawing."""
    global GRASS_COLOR_LUT
    # Create lookup table with 256 entries for smooth gradients
    GRASS_COLOR_LUT = [(0, int(config.GRASS_COLOR_MAX * i / 255), 0) for i in range(256)]

################################################
# Grass Class
################################################

class Grass:
    """Represents a grass chunk in the ecosystem.
    
    Grass serves as food for prey animals and regenerates over time
    up to a maximum amount.
    
    Attributes:
        amount: Current amount of grass in this chunk.
    """
    
    # Class-level constants (avoid instance attribute lookups)
    __slots__ = ('amount',)  # Use slots for memory efficiency and faster attribute access
    
    def __init__(self, amount: float = config.DEFAULT_GRASS_AMOUNT) -> None:
        """Initialize a grass chunk with the given amount.
        
        Args:
            amount: Initial grass amount (defaults to config value).
        """
        self.amount = amount

    def update(self) -> None:
        """Update the grass chunk, regenerating grass up to the maximum."""
        if self.amount < config.GRASS_MAX_AMOUNT:
            self.amount += config.GRASS_GROWTH_RATE
            if self.amount > config.GRASS_MAX_AMOUNT:
                self.amount = config.GRASS_MAX_AMOUNT

    def draw(self, screen: pygame.Surface, pos: tuple[int, int], size: int) -> None:
        """Draw the grass chunk as a green rectangle.
        
        Args:
            screen: The pygame surface to draw on.
            pos: The (x, y) position of the top-left corner.
            size: The size of the grass chunk in pixels.
        """
        # Use lookup table for color (fast integer index)
        lut_index = int(255 * self.amount / config.GRASS_MAX_AMOUNT)
        if lut_index > 255:
            lut_index = 255
        pygame.draw.rect(screen, GRASS_COLOR_LUT[lut_index], (pos[0], pos[1], size, size))