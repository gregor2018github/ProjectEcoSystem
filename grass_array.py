###############################################
# NumPy-based Grass Array for High Performance
###############################################

from __future__ import annotations
import numpy as np
import pygame
import config

class GrassArray:
    """High-performance grass management using NumPy arrays.
    
    Instead of individual Grass objects, this uses a 2D NumPy array
    for vectorized operations that are orders of magnitude faster.
    
    Attributes:
        cols: Number of grass columns in the world.
        rows: Number of grass rows in the world.
        amounts: 2D NumPy array of grass amounts.
        color_lut: Pre-computed color lookup table.
    """
    
    def __init__(self, cols: int, rows: int) -> None:
        """Initialize the grass array.
        
        Args:
            cols: Number of columns (world_width // chunk_size).
            rows: Number of rows (world_height // chunk_size).
        """
        self.cols = cols
        self.rows = rows
        # Initialize all grass to default amount
        self.amounts = np.full((cols, rows), config.DEFAULT_GRASS_AMOUNT, dtype=np.float32)
        
        # Pre-compute color lookup table (256 green intensity levels)
        self.color_lut = np.zeros((256, 3), dtype=np.uint8)
        for i in range(256):
            self.color_lut[i] = (0, int(config.GRASS_COLOR_MAX * i / 255), 0)
        
        # Pre-allocate surface for batch drawing (will be resized as needed)
        self._grass_surface: pygame.Surface | None = None
        self._last_visible_size: tuple[int, int] = (0, 0)
    
    def update(self) -> float:
        """Update all grass in one vectorized operation.
        
        Returns:
            The total change in grass amount (for tracking).
        """
        # Calculate how much each cell can grow (capped at max)
        old_total = self.amounts.sum()
        
        # Vectorized growth: add growth rate, then clip to max
        self.amounts += config.GRASS_GROWTH_RATE
        np.clip(self.amounts, 0, config.GRASS_MAX_AMOUNT, out=self.amounts)
        
        new_total = self.amounts.sum()
        return new_total - old_total
    
    def get_amount(self, i: int, j: int) -> float:
        """Get grass amount at a specific chunk.
        
        Args:
            i: Column index.
            j: Row index.
            
        Returns:
            Grass amount at that position, or 0 if out of bounds.
        """
        if 0 <= i < self.cols and 0 <= j < self.rows:
            return self.amounts[i, j]
        return 0.0
    
    def consume(self, i: int, j: int, amount: float = 1.0) -> float:
        """Consume grass at a specific chunk.
        
        Args:
            i: Column index.
            j: Row index.
            amount: Amount to consume.
            
        Returns:
            Actual amount consumed (may be less if not enough grass).
        """
        if 0 <= i < self.cols and 0 <= j < self.rows:
            actual = min(amount, self.amounts[i, j])
            self.amounts[i, j] -= actual
            return actual
        return 0.0
    
    def get_total(self) -> float:
        """Get total grass amount across all chunks."""
        return float(self.amounts.sum())
    
    def draw_visible(self, screen: pygame.Surface, cam_x: int, cam_y: int) -> None:
        """Draw only visible grass chunks efficiently using surface blitting.
        
        Uses NumPy array operations to build a pixel array and then scales it,
        which is much faster than drawing individual rectangles.
        
        Args:
            screen: Pygame surface to draw on.
            cam_x: Camera X offset.
            cam_y: Camera Y offset.
        """
        chunk_size = config.CHUNKSIZE
        
        # Calculate visible chunk range
        start_i = max(0, cam_x // chunk_size)
        end_i = min(self.cols, (cam_x + config.XLIM) // chunk_size + 1)
        start_j = max(0, cam_y // chunk_size)
        end_j = min(self.rows, (cam_y + config.YLIM) // chunk_size + 1)
        
        visible_width = end_i - start_i
        visible_height = end_j - start_j
        
        if visible_width <= 0 or visible_height <= 0:
            return
        
        # Get visible slice of amounts
        visible = self.amounts[start_i:end_i, start_j:end_j]
        
        # Convert amounts to color indices (0-255)
        indices = (visible * 255 / config.GRASS_MAX_AMOUNT).astype(np.uint8)
        np.clip(indices, 0, 255, out=indices)
        
        # Build RGB pixel array using the lookup table (vectorized)
        # indices shape is (width, height), we need RGB values
        pixel_colors = self.color_lut[indices]  # Shape: (width, height, 3)
        
        # Create a small surface from the pixel array
        # pygame.surfarray expects (width, height, 3) which matches our array
        small_surface = pygame.surfarray.make_surface(pixel_colors)
        
        # Scale up to actual pixel size
        scaled_width = visible_width * chunk_size
        scaled_height = visible_height * chunk_size
        scaled_surface = pygame.transform.scale(small_surface, (scaled_width, scaled_height))
        
        # Calculate screen position offset (sub-chunk alignment)
        offset_x = start_i * chunk_size - cam_x
        offset_y = start_j * chunk_size - cam_y
        
        # Blit the scaled surface to the screen
        screen.blit(scaled_surface, (offset_x, offset_y))
    
    # Dict-like interface for compatibility with existing animal code
    def get(self, key: tuple[int, int], default=None):
        """Dict-like get for compatibility."""
        i, j = key
        if 0 <= i < self.cols and 0 <= j < self.rows:
            return _GrassProxy(self, i, j)
        return default
    
    def __contains__(self, key: tuple[int, int]) -> bool:
        """Check if chunk coordinates are valid."""
        i, j = key
        return 0 <= i < self.cols and 0 <= j < self.rows
    
    def __getitem__(self, key: tuple[int, int]):
        """Get a grass proxy for compatibility."""
        i, j = key
        return _GrassProxy(self, i, j)


class _GrassProxy:
    """Lightweight proxy to provide dict-like access to grass amounts.
    
    This allows existing animal code to work without modification
    by providing an 'amount' attribute that reads/writes to the array.
    """
    __slots__ = ('_array', '_i', '_j')
    
    def __init__(self, array: GrassArray, i: int, j: int):
        self._array = array
        self._i = i
        self._j = j
    
    @property
    def amount(self) -> float:
        return self._array.amounts[self._i, self._j]
    
    @amount.setter
    def amount(self, value: float) -> None:
        self._array.amounts[self._i, self._j] = value
