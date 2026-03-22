###############################################
# Structure-of-Arrays for Animals
# Replaces list[Animal] with contiguous NumPy
# arrays for vectorized simulation updates.
###############################################

from __future__ import annotations
import numpy as np
import pygame
import config

# Global UID counter (never resets, guarantees uniqueness)
_next_uid = 0


def _alloc_uid(count: int = 1) -> int | np.ndarray:
    """Allocate one or more unique IDs."""
    global _next_uid
    if count == 1:
        uid = _next_uid
        _next_uid += 1
        return uid
    else:
        uids = np.arange(_next_uid, _next_uid + count, dtype=np.int32)
        _next_uid += count
        return uids


class PredatorArrays:
    """Structure-of-Arrays storage for all predator state."""

    SIZE = 5
    COLOR = (255, 0, 0)

    def __init__(self, capacity: int = 256) -> None:
        self.count = 0
        self.capacity = capacity

        # Identity
        self.uid = np.zeros(capacity, dtype=np.int32)

        # Position
        self.x = np.zeros(capacity, dtype=np.float32)
        self.y = np.zeros(capacity, dtype=np.float32)

        # State flags (uint8 as booleans)
        self.alive = np.ones(capacity, dtype=np.uint8)
        self.hunting = np.zeros(capacity, dtype=np.uint8)
        self.mating = np.zeros(capacity, dtype=np.uint8)
        self.reproduced = np.zeros(capacity, dtype=np.uint8)
        self.starving = np.zeros(capacity, dtype=np.uint8)
        self.killed = np.zeros(capacity, dtype=np.uint8)
        self.avoiding = np.zeros(capacity, dtype=np.uint8)

        # Scalar state
        self.food = np.zeros(capacity, dtype=np.float32)
        self.age = np.zeros(capacity, dtype=np.int32)
        self.prey_eaten = np.zeros(capacity, dtype=np.int32)
        self.offspring_created = np.zeros(capacity, dtype=np.int32)
        self.generation = np.zeros(capacity, dtype=np.int32)
        self.cur_consumption = np.zeros(capacity, dtype=np.float32)

        # Evolutionary traits
        self.speed = np.zeros(capacity, dtype=np.float32)
        self.smell_distance = np.zeros(capacity, dtype=np.float32)
        self.predator_avoid_distance = np.zeros(capacity, dtype=np.float32)
        self.max_food = np.zeros(capacity, dtype=np.float32)
        self.food_gain_per_kill = np.zeros(capacity, dtype=np.float32)
        self.regular_energy_cost = np.zeros(capacity, dtype=np.float32)
        self.hunting_energy_cost = np.zeros(capacity, dtype=np.float32)
        self.starv_border = np.zeros(capacity, dtype=np.float32)
        self.max_age = np.zeros(capacity, dtype=np.float32)
        self.high_age_health = np.zeros(capacity, dtype=np.float32)
        self.mating_search_distance = np.zeros(capacity, dtype=np.float32)

        # Mating partner index (-1 = none)
        self.mating_partner_idx = np.full(capacity, -1, dtype=np.int32)

    # All array attribute names for bulk operations
    _ARRAYS = [
        'uid', 'x', 'y', 'alive', 'hunting', 'mating', 'reproduced',
        'starving', 'killed', 'avoiding', 'food', 'age', 'prey_eaten',
        'offspring_created', 'generation', 'cur_consumption',
        'speed', 'smell_distance', 'predator_avoid_distance', 'max_food',
        'food_gain_per_kill', 'regular_energy_cost', 'hunting_energy_cost',
        'starv_border', 'max_age', 'high_age_health', 'mating_search_distance',
        'mating_partner_idx',
    ]

    def _grow(self, min_capacity: int) -> None:
        """Double capacity until >= min_capacity."""
        new_cap = self.capacity
        while new_cap < min_capacity:
            new_cap *= 2
        for name in self._ARRAYS:
            old = getattr(self, name)
            new = np.zeros(new_cap, dtype=old.dtype)
            if name == 'mating_partner_idx':
                new[:] = -1
            elif name == 'alive':
                new[:] = 1
            new[:self.count] = old[:self.count]
            setattr(self, name, new)
        self.capacity = new_cap

    def add_default(self, ax: float, ay: float, gen: int = 0) -> int:
        """Add a predator with default config traits. Returns its index."""
        if self.count >= self.capacity:
            self._grow(self.count + 1)
        i = self.count
        self.uid[i] = _alloc_uid()
        self.x[i] = ax
        self.y[i] = ay
        self.alive[i] = 1
        self.hunting[i] = 0
        self.mating[i] = 0
        self.reproduced[i] = 0
        self.starving[i] = 0
        self.killed[i] = 0
        self.avoiding[i] = 0
        self.age[i] = 0
        self.prey_eaten[i] = 0
        self.offspring_created[i] = 0
        self.generation[i] = gen
        self.cur_consumption[i] = 0.0
        self.mating_partner_idx[i] = -1

        self.speed[i] = config.PREDATOR_SPEED
        self.smell_distance[i] = config.PREDATOR_SMELL_DISTANCE
        self.predator_avoid_distance[i] = config.PREDATOR_PREDATOR_AVOID_DISTANCE
        self.max_food[i] = config.PREDATOR_MAX_FOOD
        self.food_gain_per_kill[i] = config.PREDATOR_FOOD_GAIN_PER_KILL
        self.regular_energy_cost[i] = config.PREDATOR_REGULAR_ENERGY_COST
        self.hunting_energy_cost[i] = config.PREDATOR_HUNTING_ENERGY_COST
        self.starv_border[i] = config.PREDATOR_STARV_BORDER
        self.max_age[i] = config.PREDATOR_MAX_AGE
        self.high_age_health[i] = config.PREDATOR_HIGH_AGE_HEALTH
        self.mating_search_distance[i] = config.PREDATOR_MATING_SEARCH_DISTANCE
        self.food[i] = config.PREDATOR_MAX_FOOD

        self.count += 1
        return i

    def compact(self) -> np.ndarray:
        """Remove dead entries by compacting arrays. Returns old-to-new index map."""
        n = self.count
        mask = self.alive[:n].astype(bool)
        new_count = int(mask.sum())
        if new_count == n:
            return np.arange(n, dtype=np.int32)

        # Build index remapping: old_index -> new_index (-1 if dead)
        remap = np.full(n, -1, dtype=np.int32)
        remap[mask] = np.arange(new_count, dtype=np.int32)

        for name in self._ARRAYS:
            arr = getattr(self, name)
            arr[:new_count] = arr[:n][mask]

        # Remap mating partner indices
        partners = self.mating_partner_idx[:new_count]
        valid = (partners >= 0) & (partners < n)
        partners[valid] = remap[partners[valid]]
        # Invalidate partners that were dead
        partners[partners < 0] = -1

        self.count = new_count
        return remap

    def remove_random(self) -> None:
        """Remove a random alive animal."""
        if self.count == 0:
            return
        import random
        idx = random.randrange(self.count)
        self.alive[idx] = 0
        self.compact()


class PreyArrays:
    """Structure-of-Arrays storage for all prey state."""

    SIZE = 3
    COLOR = (255, 255, 255)

    def __init__(self, capacity: int = 1024) -> None:
        self.count = 0
        self.capacity = capacity

        # Identity
        self.uid = np.zeros(capacity, dtype=np.int32)

        # Position
        self.x = np.zeros(capacity, dtype=np.float32)
        self.y = np.zeros(capacity, dtype=np.float32)

        # State flags
        self.alive = np.ones(capacity, dtype=np.uint8)
        self.mating = np.zeros(capacity, dtype=np.uint8)
        self.reproduced = np.zeros(capacity, dtype=np.uint8)
        self.starving = np.zeros(capacity, dtype=np.uint8)
        self.killed = np.zeros(capacity, dtype=np.uint8)
        self.is_fleeing = np.zeros(capacity, dtype=np.uint8)
        self.is_eating = np.zeros(capacity, dtype=np.uint8)

        # Scalar state
        self.food = np.zeros(capacity, dtype=np.float32)
        self.age = np.zeros(capacity, dtype=np.int32)
        self.grass_eaten = np.zeros(capacity, dtype=np.float32)
        self.offspring_created = np.zeros(capacity, dtype=np.int32)
        self.generation = np.zeros(capacity, dtype=np.int32)
        self.cur_consumption = np.zeros(capacity, dtype=np.float32)

        # Evolutionary traits
        self.speed = np.zeros(capacity, dtype=np.float32)
        self.fear_distance = np.zeros(capacity, dtype=np.float32)
        self.mating_simulation = np.zeros(capacity, dtype=np.uint8)
        self.mating_search_distance = np.zeros(capacity, dtype=np.float32)
        self.max_food = np.zeros(capacity, dtype=np.float32)
        self.food_gain_per_grass = np.zeros(capacity, dtype=np.float32)
        self.starv_border = np.zeros(capacity, dtype=np.float32)
        self.flee_energy_cost = np.zeros(capacity, dtype=np.float32)
        self.max_age = np.zeros(capacity, dtype=np.float32)
        self.high_age_health = np.zeros(capacity, dtype=np.float32)

        # Mating partner index
        self.mating_partner_idx = np.full(capacity, -1, dtype=np.int32)

    _ARRAYS = [
        'uid', 'x', 'y', 'alive', 'mating', 'reproduced', 'starving',
        'killed', 'is_fleeing', 'is_eating', 'food', 'age', 'grass_eaten',
        'offspring_created', 'generation', 'cur_consumption',
        'speed', 'fear_distance', 'mating_simulation', 'mating_search_distance',
        'max_food', 'food_gain_per_grass', 'starv_border', 'flee_energy_cost',
        'max_age', 'high_age_health', 'mating_partner_idx',
    ]

    def _grow(self, min_capacity: int) -> None:
        new_cap = self.capacity
        while new_cap < min_capacity:
            new_cap *= 2
        for name in self._ARRAYS:
            old = getattr(self, name)
            new = np.zeros(new_cap, dtype=old.dtype)
            if name == 'mating_partner_idx':
                new[:] = -1
            elif name == 'alive':
                new[:] = 1
            new[:self.count] = old[:self.count]
            setattr(self, name, new)
        self.capacity = new_cap

    def add_default(self, ax: float, ay: float, gen: int = 0) -> int:
        """Add a prey with default config traits. Returns its index."""
        if self.count >= self.capacity:
            self._grow(self.count + 1)
        i = self.count
        self.uid[i] = _alloc_uid()
        self.x[i] = ax
        self.y[i] = ay
        self.alive[i] = 1
        self.mating[i] = 0
        self.reproduced[i] = 0
        self.starving[i] = 0
        self.killed[i] = 0
        self.is_fleeing[i] = 0
        self.is_eating[i] = 0
        self.age[i] = 0
        self.grass_eaten[i] = 0
        self.offspring_created[i] = 0
        self.generation[i] = gen
        self.cur_consumption[i] = 0.0
        self.mating_partner_idx[i] = -1

        self.speed[i] = config.PREY_SPEED
        self.fear_distance[i] = config.PREY_FEAR_DISTANCE
        self.mating_simulation[i] = 1 if config.PREY_MATING_SIMULATION else 0
        self.mating_search_distance[i] = config.PREY_MATING_SEARCH_DISTANCE
        self.max_food[i] = config.PREY_MAX_FOOD
        self.food_gain_per_grass[i] = config.PREY_FOOD_GAIN_PER_GRASS
        self.starv_border[i] = config.PREY_STARV_BORDER
        self.flee_energy_cost[i] = config.PREY_FLEE_ENERGY_COST
        self.max_age[i] = config.PREY_MAX_AGE
        self.high_age_health[i] = config.PREY_HIGH_AGE_HEALTH
        self.food[i] = config.PREY_MAX_FOOD

        self.count += 1
        return i

    def compact(self) -> np.ndarray:
        """Remove dead entries. Returns old-to-new index remap."""
        n = self.count
        mask = self.alive[:n].astype(bool)
        new_count = int(mask.sum())
        if new_count == n:
            return np.arange(n, dtype=np.int32)

        remap = np.full(n, -1, dtype=np.int32)
        remap[mask] = np.arange(new_count, dtype=np.int32)

        for name in self._ARRAYS:
            arr = getattr(self, name)
            arr[:new_count] = arr[:n][mask]

        partners = self.mating_partner_idx[:new_count]
        valid = (partners >= 0) & (partners < n)
        partners[valid] = remap[partners[valid]]
        partners[partners < 0] = -1

        self.count = new_count
        return remap

    def remove_random(self) -> None:
        if self.count == 0:
            return
        import random
        idx = random.randrange(self.count)
        self.alive[idx] = 0
        self.compact()


###############################################
# AnimalView — thin read-only wrapper for UI
###############################################

class PredatorView:
    """Lightweight read-only view into a single predator's SoA data.

    Provides the same attribute interface as the old Predator class
    so that hover_window.py, event_handler.py, ui.py, and
    statistics_window.py work without modification.
    """

    SIZE = 5
    COLOR = (255, 0, 0)
    __class_name__ = "Predator"

    def __init__(self, arrays: PredatorArrays, index: int) -> None:
        self._a = arrays
        self._i = index

    @property
    def uid(self) -> int:
        return int(self._a.uid[self._i])

    @property
    def x(self) -> float:
        return float(self._a.x[self._i])

    @property
    def y(self) -> float:
        return float(self._a.y[self._i])

    @property
    def alive(self) -> bool:
        return bool(self._a.alive[self._i])

    @property
    def food(self) -> float:
        return float(self._a.food[self._i])

    @property
    def age(self) -> int:
        return int(self._a.age[self._i])

    @property
    def starving(self) -> bool:
        return bool(self._a.starving[self._i])

    @property
    def mating(self) -> bool:
        return bool(self._a.mating[self._i])

    @property
    def hunting(self) -> bool:
        return bool(self._a.hunting[self._i])

    @property
    def avoiding_predator_flag(self) -> bool:
        return bool(self._a.avoiding[self._i])

    @property
    def killed(self) -> bool:
        return bool(self._a.killed[self._i])

    @property
    def prey_eaten(self) -> int:
        return int(self._a.prey_eaten[self._i])

    @property
    def offspring_created(self) -> int:
        return int(self._a.offspring_created[self._i])

    @property
    def generation(self) -> int:
        return int(self._a.generation[self._i])

    @property
    def cur_consumption(self) -> float:
        return float(self._a.cur_consumption[self._i])

    @property
    def max_food(self) -> float:
        return float(self._a.max_food[self._i])

    # Evolutionary traits (accessed by statistics_window.py via getattr)
    @property
    def speed(self) -> float:
        return float(self._a.speed[self._i])

    @property
    def smell_distance(self) -> float:
        return float(self._a.smell_distance[self._i])

    @property
    def predator_avoid_distance(self) -> float:
        return float(self._a.predator_avoid_distance[self._i])

    @property
    def food_gain_per_kill(self) -> float:
        return float(self._a.food_gain_per_kill[self._i])

    @property
    def regular_energy_cost(self) -> float:
        return float(self._a.regular_energy_cost[self._i])

    @property
    def hunting_energy_cost(self) -> float:
        return float(self._a.hunting_energy_cost[self._i])

    @property
    def starv_border(self) -> float:
        return float(self._a.starv_border[self._i])

    @property
    def max_age(self) -> float:
        return float(self._a.max_age[self._i])

    @property
    def high_age_health(self) -> float:
        return float(self._a.high_age_health[self._i])

    @property
    def mating_search_distance(self) -> float:
        return float(self._a.mating_search_distance[self._i])

    # Methods expected by UI code
    def get_status(self) -> str:
        if not self.alive:
            return "Deceased"
        if self.hunting:
            return "Hunting"
        if self.mating:
            return "Mating"
        if self.avoiding_predator_flag:
            return "Avoiding Predator"
        if self.starving:
            return "Starving"
        return "Idle"

    def get_screen_rect(self) -> pygame.Rect:
        screen_x = int(self.x - config.camera_x)
        screen_y = int(self.y - config.camera_y)
        return pygame.Rect(screen_x - self.SIZE, screen_y - self.SIZE, 2 * self.SIZE, 2 * self.SIZE)

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.SIZE, self.y - self.SIZE, 2 * self.SIZE, 2 * self.SIZE)

    def draw(self, screen: pygame.Surface) -> None:
        screen_x = int(self.x - config.camera_x)
        screen_y = int(self.y - config.camera_y)
        if -self.SIZE <= screen_x <= config.XLIM + self.SIZE and -self.SIZE <= screen_y <= config.YLIM + self.SIZE:
            pygame.draw.circle(screen, self.COLOR, (screen_x, screen_y), self.SIZE)

    @property
    def __class__(self):
        """Make isinstance checks and __class__.__name__ work for UI code."""
        return _PredatorFakeClass


class PreyView:
    """Lightweight read-only view into a single prey's SoA data."""

    SIZE = 3
    COLOR = (255, 255, 255)
    __class_name__ = "Prey"

    def __init__(self, arrays: PreyArrays, index: int) -> None:
        self._a = arrays
        self._i = index

    @property
    def uid(self) -> int:
        return int(self._a.uid[self._i])

    @property
    def x(self) -> float:
        return float(self._a.x[self._i])

    @property
    def y(self) -> float:
        return float(self._a.y[self._i])

    @property
    def alive(self) -> bool:
        return bool(self._a.alive[self._i])

    @property
    def food(self) -> float:
        return float(self._a.food[self._i])

    @property
    def age(self) -> int:
        return int(self._a.age[self._i])

    @property
    def starving(self) -> bool:
        return bool(self._a.starving[self._i])

    @property
    def mating(self) -> bool:
        return bool(self._a.mating[self._i])

    @property
    def is_fleeing(self) -> bool:
        return bool(self._a.is_fleeing[self._i])

    @property
    def is_eating(self) -> bool:
        return bool(self._a.is_eating[self._i])

    @property
    def killed(self) -> bool:
        return bool(self._a.killed[self._i])

    @property
    def grass_eaten(self) -> float:
        return float(self._a.grass_eaten[self._i])

    @property
    def offspring_created(self) -> int:
        return int(self._a.offspring_created[self._i])

    @property
    def generation(self) -> int:
        return int(self._a.generation[self._i])

    @property
    def cur_consumption(self) -> float:
        return float(self._a.cur_consumption[self._i])

    @property
    def max_food(self) -> float:
        return float(self._a.max_food[self._i])

    # Evolutionary traits
    @property
    def speed(self) -> float:
        return float(self._a.speed[self._i])

    @property
    def fear_distance(self) -> float:
        return float(self._a.fear_distance[self._i])

    @property
    def mating_simulation(self) -> bool:
        return bool(self._a.mating_simulation[self._i])

    @property
    def mating_search_distance(self) -> float:
        return float(self._a.mating_search_distance[self._i])

    @property
    def food_gain_per_grass(self) -> float:
        return float(self._a.food_gain_per_grass[self._i])

    @property
    def starv_border(self) -> float:
        return float(self._a.starv_border[self._i])

    @property
    def flee_energy_cost(self) -> float:
        return float(self._a.flee_energy_cost[self._i])

    @property
    def max_age(self) -> float:
        return float(self._a.max_age[self._i])

    @property
    def high_age_health(self) -> float:
        return float(self._a.high_age_health[self._i])

    def get_status(self) -> str:
        if not self.alive:
            return "Deceased"
        if self.is_fleeing:
            return "Fleeing"
        if self.mating:
            return "Mating"
        if self.is_eating:
            return "Eating Grass"
        if self.starving:
            return "Starving"
        return "Idle"

    def get_screen_rect(self) -> pygame.Rect:
        screen_x = int(self.x - config.camera_x)
        screen_y = int(self.y - config.camera_y)
        return pygame.Rect(screen_x - self.SIZE, screen_y - self.SIZE, 2 * self.SIZE, 2 * self.SIZE)

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.SIZE, self.y - self.SIZE, 2 * self.SIZE, 2 * self.SIZE)

    def draw(self, screen: pygame.Surface) -> None:
        screen_x = int(self.x - config.camera_x)
        screen_y = int(self.y - config.camera_y)
        if -self.SIZE <= screen_x <= config.XLIM + self.SIZE and -self.SIZE <= screen_y <= config.YLIM + self.SIZE:
            pygame.draw.circle(screen, self.COLOR, (screen_x, screen_y), self.SIZE)

    @property
    def __class__(self):
        return _PreyFakeClass


###############################################
# Fake classes for isinstance() compatibility
###############################################

class _PredatorFakeClass:
    """Sentinel so isinstance(view, Predator) checks in hover_window work via __class__."""
    __name__ = "Predator"

class _PreyFakeClass:
    __name__ = "Prey"


def build_predator_views(arrays: PredatorArrays) -> list[PredatorView]:
    """Build a list of PredatorView wrappers for all alive predators."""
    return [PredatorView(arrays, i) for i in range(arrays.count)]


def build_prey_views(arrays: PreyArrays) -> list[PreyView]:
    """Build a list of PreyView wrappers for all alive prey."""
    return [PreyView(arrays, i) for i in range(arrays.count)]


def find_view_by_uid(views: list, target_uid: int):
    """Find a view with the given uid, or return None."""
    for v in views:
        if v.uid == target_uid:
            return v
    return None
