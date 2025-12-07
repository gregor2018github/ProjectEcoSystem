
###############################################
# Imports
###############################################

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import pygame
import random
import config

if TYPE_CHECKING:
    from grass_array import GrassArray

###############################################
# General animal class definition
###############################################

class Animal(ABC):
    """Abstract base class representing an animal in the ecosystem.
    
    Attributes:
        x: The x-coordinate of the animal's position.
        y: The y-coordinate of the animal's position.
        alive: Whether the animal is alive.
        starving: Whether the animal is currently starving.
        killed: Whether the animal killed another animal this round.
        age: The age of the animal in simulation ticks.
        cur_consumption: The current energy consumption rate.
    """
    
    SIZE: int  # Must be defined in subclasses
    
    def __init__(self, x: float, y: float) -> None:
        """Initialize an animal at the given position.
        
        Args:
            x: The initial x-coordinate.
            y: The initial y-coordinate.
        """
        self.x = x
        self.y = y
        self.alive = True
        self.starving = False  # attribute to track starvation
        self.killed = False  # attribute to track kill events
        self.age = 0
        self.cur_consumption = 0.0  

    def get_rect(self) -> pygame.Rect:
        """Get the bounding rectangle for this animal in world coordinates.
        
        Returns:
            A pygame.Rect representing the animal's bounding box in world coordinates.
        """
        return pygame.Rect(self.x - self.SIZE, self.y - self.SIZE, 2 * self.SIZE, 2 * self.SIZE)

    def get_screen_rect(self) -> pygame.Rect:
        """Get the bounding rectangle for this animal in screen coordinates.
        
        Accounts for the camera offset to return the position as it appears on screen.
        
        Returns:
            A pygame.Rect representing the animal's bounding box in screen coordinates.
        """
        screen_x = int(self.x - config.camera_x)
        screen_y = int(self.y - config.camera_y)
        return pygame.Rect(screen_x - self.SIZE, screen_y - self.SIZE, 2 * self.SIZE, 2 * self.SIZE)

    @abstractmethod
    def get_status(self) -> str:
        """Get a string describing the animal's current status.
        
        Returns:
            A string describing the current status (e.g., 'Hunting', 'Fleeing', 'Idle').
        """
        pass

    def consumed_all_energy(self) -> bool:
        """Check if the animal has consumed all its energy.
        
        Calculates energy consumption based on the animal type (Predator or Prey)
        and its current state (hunting/fleeing or not). Updates the starving flag
        if the animal's food level falls below the starvation threshold.
        
        Returns:
            True if the animal has run out of energy and should die, False otherwise.
        """
        if isinstance(self, Predator):
            # Predator energy consumption logic
            if self.hunting:
                self.cur_consumption = config.PREDATOR_HUNTING_ENERGY_COST
            else:
                self.cur_consumption = config.PREDATOR_REGULAR_ENERGY_COST
        else:
            # Prey energy consumption logic
            if self.is_fleeing:
                self.cur_consumption = config.PREY_FLEE_ENERGY_COST
            else:
                self.cur_consumption = config.PREY_REGULAR_ENERGY_COST

        # Reduce food based on current consumption        
        self.food -= self.cur_consumption
        if self.food <= 0:
            return True  # Mark as dead if food is depleted
        else: # else check if the animal is starving
            if isinstance(self, Predator):
                # Predator starvation check
                if self.food < config.PREDATOR_STARV_BORDER * config.PREDATOR_MAX_FOOD:
                    self.starving = True
                else:
                    self.starving = False
            else:
                # Prey starvation check
                if self.food < config.PREY_STARV_BORDER * config.PREY_MAX_FOOD:
                    self.starving = True
                else:
                    self.starving = False
        return False  # Mark as alive if food is not depleted

    @abstractmethod
    def update(self, animals: list[Animal], grass: GrassArray) -> None:
        """Update the animal's state for one simulation tick.
        
        Args:
            animals: List of all animals in the simulation.
            grass: GrassArray for grass management.
        """
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the animal on the screen.
        
        Args:
            screen: The pygame surface to draw on.
        """
        pass

###############################################
# Predators
###############################################

class Predator(Animal):
    """A predator animal that hunts prey in the ecosystem.
    
    Attributes:
        COLOR: The color used to draw the predator (red).
        SIZE: The radius of the predator in pixels.
        food: Current food/energy level.
        hunting: Whether the predator is currently hunting.
        avoiding_predator_flag: Whether the predator is avoiding other predators.
        prey_eaten: Total number of prey eaten by this predator.
    """
    
    COLOR: tuple[int, int, int] = (255, 0, 0)  # Red
    SIZE: int = 5

    def __init__(self, x: float, y: float) -> None:
        """Initialize a predator at the given position.
        
        Args:
            x: The initial x-coordinate.
            y: The initial y-coordinate.
        """
        super().__init__(x, y)
        self.food = config.PREDATOR_MAX_FOOD  # Initialize predator food
        self.hunting = False  # attribute to track hunting state
        self.avoiding_predator_flag = False # For status display
        self.prey_eaten = 0

    def get_status(self) -> str:
        """Get a string describing the predator's current status.
        
        Returns:
            A string indicating the predator's state: 'Deceased', 'Hunting',
            'Avoiding Predator', 'Starving', or 'Idle'.
        """
        if not self.alive:
            return "Deceased"
        if self.hunting:
            return "Hunting"
        if self.avoiding_predator_flag:
            return "Avoiding Predator"
        if self.starving:
            return "Starving"
        return "Idle"
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the predator as a red circle on the screen.
        
        Args:
            screen: The pygame surface to draw on.
        """
        # Apply camera offset for drawing
        screen_x = int(self.x - config.camera_x)
        screen_y = int(self.y - config.camera_y)
        # Only draw if visible on screen
        if -self.SIZE <= screen_x <= config.XLIM + self.SIZE and -self.SIZE <= screen_y <= config.YLIM + self.SIZE:
            pygame.draw.circle(screen, self.COLOR, (screen_x, screen_y), self.SIZE)
    
    def update(self, predators: list[Predator], preys: list[Prey], grass: GrassArray) -> None:
        """Update the predator's state for one simulation tick.
        
        Handles aging, energy consumption, predator avoidance, hunting behavior,
        and random movement. The predator will hunt prey when hungry, avoid
        other predators when not starving, and move randomly when idle.
        
        Args:
            predators: List of all predators in the simulation.
            preys: List of all prey in the simulation.
            grass: GrassArray for grass management (unused by predators).
        """
        self.killed = False # means it killed something this round
        self.avoiding_predator_flag = False # Reset at the start of each update cycle
        target = None
        min_dist_prey = float('inf')
        avoid_dx = 0
        avoid_dy = 0
        predator_too_close = False

        # check for death by age
        self.age += 1
        if self.age > config.PREDATOR_MAX_AGE:
            if random.uniform(0, 1) > config.PREDATOR_HIGH_AGE_HEALTH: # x% chance to die of old age
                self.alive = False
                config.predator_dead_by_age += 1
                return
        # check for death by starvation
        if self.consumed_all_energy():  # Reduce food and possibly mark dead or starving
            self.alive = False
            config.predator_dead_by_starvation += 1
            return

        # Separate moving loops for evading predators, hunting prey, and moving randomly
        
        # Check for nearby predators and calculate avoidance vector
        if config.PRED_AVOID_PRED:
            for other in predators:
                if other is not self:
                    dx = self.x - other.x  # Vector pointing away from the other predator
                    dy = self.y - other.y
                    dist_sq = dx**2 + dy**2 # Use squared distance for efficiency
                    if dist_sq < config.PREDATOR_PREDATOR_AVOID_DISTANCE**2 and dist_sq != 0:
                        predator_too_close = True
                        dist = dist_sq**0.5
                        # Add normalized vector pointing away, weighted by inverse distance (stronger avoidance for closer predators)
                        avoid_dx += dx / dist 
                        avoid_dy += dy / dist
        
        # If avoiding predators, move away and skip hunting, but only if not starving
        if config.PRED_AVOID_PRED and predator_too_close and not self.starving:
            self.hunting = False
            self.avoiding_predator_flag = True # Set status flag
            norm = (avoid_dx**2 + avoid_dy**2)**0.5 or 1 # Normalize the total avoidance vector
            self.x += (avoid_dx / norm) * config.PREDATOR_SPEED 
            self.y += (avoid_dy / norm) * config.PREDATOR_SPEED
        else:
            # Find the closest prey - iterate directly over preys list (no isinstance needed)
            for prey in preys:
                dx = prey.x - self.x
                dy = prey.y - self.y
                dist = (dx**2 + dy**2)**0.5
                # check if prey is in smell distance
                if dist < config.PREDATOR_SMELL_DISTANCE:
                    # Check if prey is closer than the current target
                    if dist < min_dist_prey:
                        min_dist_prey = dist
                        target = prey
            # If a target is found, move towards it
            if target:
                self.hunting = True
                dx = target.x - self.x
                dy = target.y - self.y
                # dist is already calculated as min_dist_prey
                dist_norm = min_dist_prey or 1 # Avoid division by zero
                self.x += (dx / dist_norm) * config.PREDATOR_SPEED
                self.y += (dy / dist_norm) * config.PREDATOR_SPEED
                
                # Check for kill
                if min_dist_prey < self.SIZE + target.SIZE: # No need to check target.alive again, done in prey finding loop
                    target.alive = False
                    self.killed = True  # Mark kill for reproduction
                    self.prey_eaten += 1
                    config.prey_dead_by_hunting += 1
                    # Add food gain on kill; cap to max
                    self.food = min(config.PREDATOR_MAX_FOOD, self.food + config.PREDATOR_FOOD_GAIN_PER_KILL)
            # if not hunting, move randomly
            else:
                self.hunting = False
                self.x += random.uniform(-1, 1)
                self.y += random.uniform(-1, 1)

        # Boundary checks (use world size, not screen size)
        self.x = max(0, min(config.WORLD_WIDTH, self.x))
        self.y = max(0, min(config.WORLD_HEIGHT, self.y))

###############################################
# Prey 
###############################################

class Prey(Animal):
    """A prey animal that eats grass and flees from predators.
    
    Attributes:
        COLOR: The color used to draw the prey (white).
        SIZE: The radius of the prey in pixels.
        food: Current food/energy level.
        is_fleeing: Whether the prey is currently fleeing from a predator.
        is_eating: Whether the prey is currently eating grass.
        grass_eaten: Total amount of grass eaten by this prey.
    """
    
    COLOR: tuple[int, int, int] = (255, 255, 255)  # White
    SIZE: int = 3

    def __init__(self, x: float, y: float) -> None:
        """Initialize a prey animal at the given position.
        
        Args:
            x: The initial x-coordinate.
            y: The initial y-coordinate.
        """
        super().__init__(x, y)
        self.food = config.PREY_MAX_FOOD  # Initialize prey food
        self.is_fleeing = False
        self.is_eating = False
        self.grass_eaten = 0
    
    def get_status(self) -> str:
        """Get a string describing the prey's current status.
        
        Returns:
            A string indicating the prey's state: 'Deceased', 'Fleeing',
            'Eating Grass', 'Starving', or 'Idle'.
        """
        if not self.alive:
            return "Deceased"
        if self.is_fleeing:
            return "Fleeing"
        if self.is_eating: # Eating takes precedence over starving if both are true
            return "Eating Grass"
        if self.starving:
            return "Starving"
        return "Idle"

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the prey as a white circle on the screen.
        
        Args:
            screen: The pygame surface to draw on.
        """
        # Apply camera offset for drawing
        screen_x = int(self.x - config.camera_x)
        screen_y = int(self.y - config.camera_y)
        # Only draw if visible on screen
        if -self.SIZE <= screen_x <= config.XLIM + self.SIZE and -self.SIZE <= screen_y <= config.YLIM + self.SIZE:
            pygame.draw.circle(screen, self.COLOR, (screen_x, screen_y), self.SIZE)
  
    def update(self, predators: list[Predator], grass: GrassArray) -> None:
        """Update the prey's state for one simulation tick.
        
        Handles aging, fleeing from predators, energy consumption, movement
        towards areas with more grass, and eating grass to gain energy.
        
        Args:
            predators: List of all predators in the simulation.
            grass: GrassArray for grass management.
        """
        # Reset status flags at the beginning of each update
        self.is_fleeing = False
        self.is_eating = False

        # check for death by age
        self.age += 1
        if self.age > config.PREY_MAX_AGE:
            if random.uniform(0, 1) > config.PREY_HIGH_AGE_HEALTH:  # x% chance to die of old age
                self.alive = False
                config.prey_dead_by_age += 1
                return

        # Flee from predators (animal flees first, then the cost of moving is calculated)
        flee_dx = 0
        flee_dy = 0
        for predator in predators:
            dx = self.x - predator.x
            dy = self.y - predator.y
            dist = (dx**2 + dy**2) ** 0.5
            if dist < config.PREY_FEAR_DISTANCE and dist != 0:
                flee_dx += dx / dist
                flee_dy += dy / dist
        if flee_dx or flee_dy:
            norm = (flee_dx**2 + flee_dy**2) ** 0.5 or 1
            self.x += (flee_dx / norm) * config.PREY_SPEED
            self.y += (flee_dy / norm) * config.PREY_SPEED
            self.is_fleeing = True # Set status flag
        else:
            self.x += random.uniform(-1, 1)
            self.y += random.uniform(-1, 1)
        
        # check for death by starvation
        if self.consumed_all_energy():  # Reduce food and possibly mark dead or starving
            self.alive = False
            config.prey_dead_by_starvation += 1
            return
        
        # Move away from areas with little grass
        chunk = (int(self.x) // config.CHUNKSIZE, int(self.y) // config.CHUNKSIZE)
        if chunk in grass:
            current_amount = grass[chunk].amount
            grass_dx, grass_dy = 0, 0
            # Look in a 3x3 grid
            for i in [-1, 0, 1]:
                for j in [-1, 0, 1]:
                    if i == 0 and j == 0:
                        continue
                    neighbor = (chunk[0] + i, chunk[1] + j)
                    if neighbor in grass:
                        diff = grass[neighbor].amount - current_amount
                        # Only add if neighbor has more grass
                        if diff > 0:
                            grass_dx += i * diff
                            grass_dy += j * diff
            if grass_dx != 0 or grass_dy != 0:
                norm = (grass_dx**2 + grass_dy**2) ** 0.5 or 1
                # Scale the adjustment (using half of PREY_SPEED)
                self.x += (grass_dx / norm) * (config.PREY_SPEED * 0.5)
                self.y += (grass_dy / norm) * (config.PREY_SPEED * 0.5)
        
        # Boundary checks (use world size, not screen size)
        self.x = max(0, min(config.WORLD_WIDTH, self.x))
        self.y = max(0, min(config.WORLD_HEIGHT, self.y))
        # Consume grass and gain food based on current patch
        if chunk in grass:
            gain = grass[chunk].amount * config.PREY_FOOD_GAIN_PER_GRASS
            # Prey is eating if it gains food and is not full, and grass is available
            if gain > 0 and self.food < config.PREY_MAX_FOOD and grass[chunk].amount > 0:
                self.is_eating = True
                self.grass_eaten += gain
            self.food = min(config.PREY_MAX_FOOD, self.food + gain)
            # Track grass consumed for global total
            grass_consumed = min(1, grass[chunk].amount)  # Can't consume more than available
            grass[chunk].amount = max(0, grass[chunk].amount - 1)
            config.total_grass -= grass_consumed

