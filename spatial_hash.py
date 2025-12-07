###############################################
# Spatial Hash Grid for Fast Proximity Queries
###############################################

from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Generic
from collections import defaultdict

if TYPE_CHECKING:
    from animals import Animal, Predator, Prey

T = TypeVar('T')


class SpatialHash(Generic[T]):
    """A spatial hash grid for fast proximity queries.
    
    Divides the world into cells and allows O(1) lookup of nearby entities
    instead of O(n) brute force distance checks.
    
    Attributes:
        cell_size: Size of each cell in pixels.
        grid: Dictionary mapping (cell_x, cell_y) to list of entities.
    """
    
    __slots__ = ('cell_size', 'grid')
    
    def __init__(self, cell_size: float) -> None:
        """Initialize the spatial hash.
        
        Args:
            cell_size: Size of each cell. Should be >= the largest query distance.
        """
        self.cell_size = cell_size
        self.grid: dict[tuple[int, int], list[T]] = defaultdict(list)
    
    def clear(self) -> None:
        """Clear all entities from the grid."""
        self.grid.clear()
    
    def _get_cell(self, x: float, y: float) -> tuple[int, int]:
        """Get the cell coordinates for a position."""
        return (int(x // self.cell_size), int(y // self.cell_size))
    
    def insert(self, entity: T, x: float, y: float) -> None:
        """Insert an entity at the given position.
        
        Args:
            entity: The entity to insert.
            x: X coordinate.
            y: Y coordinate.
        """
        cell = self._get_cell(x, y)
        self.grid[cell].append(entity)
    
    def get_nearby(self, x: float, y: float, radius: float) -> list[T]:
        """Get all entities within a radius of the given position.
        
        Args:
            x: X coordinate of the query point.
            y: Y coordinate of the query point.
            radius: Maximum distance to search.
            
        Returns:
            List of entities within the radius (may include some beyond radius).
        """
        result: list[T] = []
        # How many cells to check in each direction
        cells_to_check = int(radius // self.cell_size) + 1
        center_cell = self._get_cell(x, y)
        
        for di in range(-cells_to_check, cells_to_check + 1):
            for dj in range(-cells_to_check, cells_to_check + 1):
                cell = (center_cell[0] + di, center_cell[1] + dj)
                if cell in self.grid:
                    result.extend(self.grid[cell])
        
        return result
    
    def build_from_list(self, entities: list[T]) -> None:
        """Build the grid from a list of entities with x, y attributes.
        
        Args:
            entities: List of entities with x and y attributes.
        """
        self.clear()
        for entity in entities:
            self.insert(entity, entity.x, entity.y)  # type: ignore
