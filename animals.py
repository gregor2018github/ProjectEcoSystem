
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
    from spatial_hash import SpatialHash

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
        self.mating = False  # True if animal is trying to mate this round
        self.reproduced = False  # animal can raise reproduction signal to simulation module (there new animal will be spawned)
        self.mating_partner: Animal | None = None  # Reference to mating partner for trait inheritance
        self.age = 0
        self.cur_consumption = 0.0
        self.generation = 0  # Track generation for statistics  
        self.offspring_created = 0  # Total number of offspring created by this animal

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
                self.cur_consumption = self.hunting_energy_cost
            else:
                self.cur_consumption = self.regular_energy_cost
        else:
            # Prey energy consumption logic
            if self.is_fleeing:
                self.cur_consumption = self.flee_energy_cost
            else:
                self.cur_consumption = config.PREY_REGULAR_ENERGY_COST

        # Reduce food based on current consumption        
        self.food -= self.cur_consumption
        if self.food <= 0:
            return True  # Mark as dead if food is depleted
        else: # else check if the animal is starving
            # Use instance variables for starvation check
            if self.food < self.starv_border * self.max_food:
                self.starving = True
            else:
                self.starving = False
        return False  # Mark as alive if food is not depleted

    @abstractmethod
    def update(self, *args, **kwargs) -> None:
        """Update the animal's state for one simulation tick.
        
        Args:
            Subclass-specific arguments for spatial hashes and grass.
        """
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the animal on the screen.
        
        Args:
            screen: The pygame surface to draw on.
        """
        pass

    @abstractmethod
    def inherit_traits(self, partner: Animal) -> Animal:
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

    def __init__(self, x: float, y: float, generation: int=0) -> None:
        """Initialize a predator at the given position.
        
        Args:
            x: The initial x-coordinate.
            y: The initial y-coordinate.
        """
        super().__init__(x, y)
        
        # Evolutionary traits (can vary between individuals)
        self.speed = config.PREDATOR_SPEED
        self.predator_avoid_distance = config.PREDATOR_PREDATOR_AVOID_DISTANCE
        self.smell_distance = config.PREDATOR_SMELL_DISTANCE
        self.max_food = config.PREDATOR_MAX_FOOD
        self.food_gain_per_kill = config.PREDATOR_FOOD_GAIN_PER_KILL
        self.regular_energy_cost = config.PREDATOR_REGULAR_ENERGY_COST
        self.hunting_energy_cost = config.PREDATOR_HUNTING_ENERGY_COST
        self.starv_border = config.PREDATOR_STARV_BORDER
        self.max_age = config.PREDATOR_MAX_AGE
        self.high_age_health = config.PREDATOR_HIGH_AGE_HEALTH
        self.mating_search_distance = config.PREDATOR_MATING_SEARCH_DISTANCE
        
        self.food = self.max_food  # Initialize predator food
        self.hunting = False  # attribute to track hunting state
        self.avoiding_predator_flag = False # For status display
        self.prey_eaten = 0
        self.generation = generation  # Track generation for statistics

    def get_status(self) -> str:
        """Get a string describing the predator's current status.
        
        Returns:
            A string indicating the predator's state: 'Deceased', 'Hunting',
            'Mating', 'Avoiding Predator', 'Starving', or 'Idle'.
        """
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
    
    def update(self, predator_hash: SpatialHash[Predator], prey_hash: SpatialHash[Prey], grass: GrassArray) -> None:
        """Update the predator's state for one simulation tick.
        
        Handles aging, energy consumption, predator avoidance, hunting behavior,
        mating behavior, and random movement. The predator will hunt prey when hungry,
        avoid other predators when not starving or mating, search for mates after
        a kill, and move randomly when idle.
        
        Args:
            predator_hash: Spatial hash of all predators for fast proximity queries.
            prey_hash: Spatial hash of all prey for fast proximity queries.
            grass: GrassArray for grass management (unused by predators).
        """
        self.killed = False # means it killed something this round
        self.reproduced = False  # Reset reproduction flag
        self.avoiding_predator_flag = False # Reset at the start of each update cycle
        target = None
        min_dist_prey = float('inf')
        avoid_dx = 0
        avoid_dy = 0
        predator_too_close = False

        # check for death by age
        self.age += 1
        if self.age > self.max_age:
            if random.uniform(0, 1) > self.high_age_health: # x% chance to die of old age
                self.alive = False
                config.predator_dead_by_age += 1
                return
        # check for death by starvation
        if self.consumed_all_energy():  # Reduce food and possibly mark dead or starving
            self.alive = False
            config.predator_dead_by_starvation += 1
            return
        
        # Starving predators lose their mating flag - survival takes priority
        if self.starving:
            self.mating = False

        # Separate moving loops for evading predators, hunting prey, mating, and moving randomly
        
        # Check for nearby predators and calculate avoidance vector (using spatial hash)
        if config.PRED_AVOID_PRED:
            nearby_predators = predator_hash.get_nearby(self.x, self.y, self.predator_avoid_distance)
            for other in nearby_predators:
                if other is not self:
                    dx = self.x - other.x  # Vector pointing away from the other predator
                    dy = self.y - other.y
                    dist_sq = dx*dx + dy*dy # Use squared distance for efficiency
                    if dist_sq < self.predator_avoid_distance**2 and dist_sq != 0:
                        predator_too_close = True
                        dist = dist_sq**0.5
                        # Add normalized vector pointing away, weighted by inverse distance (stronger avoidance for closer predators)
                        avoid_dx += dx / dist 
                        avoid_dy += dy / dist
        
        # If avoiding predators, move away and skip hunting, but only if not starving and not mating
        if config.PRED_AVOID_PRED and predator_too_close and not self.starving and not self.mating:
            self.hunting = False
            self.avoiding_predator_flag = True # Set status flag
            norm = (avoid_dx*avoid_dx + avoid_dy*avoid_dy)**0.5 or 1 # Normalize the total avoidance vector
            self.x += (avoid_dx / norm) * self.speed 
            self.y += (avoid_dy / norm) * self.speed
        else:
            # Try to find a mate if in mating mode
            mate_found = False
            if self.mating:
                self.hunting = False
                # Find nearby mating predators using spatial hash for efficiency
                nearby_predators = predator_hash.get_nearby(self.x, self.y, self.mating_search_distance)
                
                best_mate = None
                min_dist_sq = float('inf')
                
                for other in nearby_predators:
                    if other is self or not other.mating or not other.alive:
                        continue
                    dx = other.x - self.x
                    dy = other.y - self.y
                    dist_sq = dx*dx + dy*dy
                    if dist_sq < self.mating_search_distance**2 and dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        best_mate = other
                
                if best_mate:
                    mate_found = True
                    # Check if close enough to mate
                    if min_dist_sq <= config.PREDATOR_MATING_CLOSE_DISTANCE**2:
                        # Mating successful! One predator reproduces, both stop mating
                        self.reproduced = True
                        self.mating_partner = best_mate  # Store partner for trait inheritance
                        self.mating = False
                        best_mate.mating = False
                    else:
                        # Move towards the mate
                        dist = min_dist_sq ** 0.5 or 1
                        dx = best_mate.x - self.x
                        dy = best_mate.y - self.y
                        self.x += (dx / dist) * self.speed
                        self.y += (dy / dist) * self.speed
            
            # If not mating or no mate found, try to hunt
            if not mate_found:
                # Find the closest prey using spatial hash
                nearby_preys = prey_hash.get_nearby(self.x, self.y, self.smell_distance)
                for prey in nearby_preys:
                    dx = prey.x - self.x
                    dy = prey.y - self.y
                    dist_sq = dx*dx + dy*dy
                    # check if prey is in smell distance (using squared distance)
                    if dist_sq < self.smell_distance**2:
                        # Check if prey is closer than the current target
                        if dist_sq < min_dist_prey:
                            min_dist_prey = dist_sq
                            target = prey
                
                # Convert squared distance to actual distance if we found a target
                if target:
                    min_dist_prey = min_dist_prey**0.5
                
                # If a target is found, move towards it
                if target:
                    self.hunting = True
                    dx = target.x - self.x
                    dy = target.y - self.y
                    # dist is already calculated as min_dist_prey
                    dist_norm = min_dist_prey or 1 # Avoid division by zero
                    self.x += (dx / dist_norm) * self.speed
                    self.y += (dy / dist_norm) * self.speed
                    
                    # Check for kill
                    if min_dist_prey < self.SIZE + target.SIZE: # No need to check target.alive again, done in prey finding loop
                        target.alive = False
                        self.killed = True  # Mark kill event
                        self.mating = True  # Enter mating mode after a kill
                        self.prey_eaten += 1
                        config.prey_dead_by_hunting += 1
                        # Add food gain on kill; cap to max
                        self.food = min(self.max_food, self.food + self.food_gain_per_kill)
                # if not hunting, move randomly
                else:
                    self.hunting = False
                    self.x += random.uniform(-1, 1)
                    self.y += random.uniform(-1, 1)

        # Boundary checks (use world size, not screen size)
        self.x = max(0, min(config.WORLD_WIDTH, self.x))
        self.y = max(0, min(config.WORLD_HEIGHT, self.y))

    def inherit_traits(self, partner: Predator) -> Predator:
        """Create a new predator with traits inherited from this predator and a partner.
        
        The child's trait value is calculated as:
        1. Random value between parent1's trait and parent2's trait
        2. Plus/minus a random mutation (±MUTATION_RATE * base_value from config)
        
        Using base values for mutation prevents multiplicative drift.
        
        Args:
            partner: The other parent predator.
            
        Returns:
            A new Predator with inherited traits.
        """
        child = Predator(self.x, self.y, generation=max(self.generation, partner.generation) + 1)
        
        # Helper function to inherit a trait with mutation
        def inherit_trait(p1_val: float, p2_val: float, base_val: float) -> float:
            # Random value between the two parents
            inherited = random.uniform(min(p1_val, p2_val), max(p1_val, p2_val))
            # Mutation: ±(MUTATION_RATE * base_value) to prevent multiplicative drift
            mutation = random.uniform(-config.MUTATION_RATE, config.MUTATION_RATE) * base_val
            return max(0.001, inherited + mutation)  # Ensure positive values
        
        # Inherit all evolutionary traits
        child.speed = inherit_trait(self.speed, partner.speed, config.PREDATOR_SPEED)
        child.predator_avoid_distance = inherit_trait(
            self.predator_avoid_distance, partner.predator_avoid_distance, 
            config.PREDATOR_PREDATOR_AVOID_DISTANCE
        )
        child.smell_distance = inherit_trait(
            self.smell_distance, partner.smell_distance, config.PREDATOR_SMELL_DISTANCE
        )
        child.max_food = inherit_trait(self.max_food, partner.max_food, config.PREDATOR_MAX_FOOD)
        child.food_gain_per_kill = inherit_trait(
            self.food_gain_per_kill, partner.food_gain_per_kill, config.PREDATOR_FOOD_GAIN_PER_KILL
        )
        child.regular_energy_cost = inherit_trait(
            self.regular_energy_cost, partner.regular_energy_cost, config.PREDATOR_REGULAR_ENERGY_COST
        )
        child.hunting_energy_cost = inherit_trait(
            self.hunting_energy_cost, partner.hunting_energy_cost, config.PREDATOR_HUNTING_ENERGY_COST
        )
        child.starv_border = inherit_trait(
            self.starv_border, partner.starv_border, config.PREDATOR_STARV_BORDER
        )
        child.max_age = inherit_trait(self.max_age, partner.max_age, config.PREDATOR_MAX_AGE)
        child.high_age_health = min(1.0, inherit_trait(
            self.high_age_health, partner.high_age_health, config.PREDATOR_HIGH_AGE_HEALTH
        ))  # Cap at 1.0 for probability
        child.mating_search_distance = inherit_trait(
            self.mating_search_distance, partner.mating_search_distance, 
            config.PREDATOR_MATING_SEARCH_DISTANCE
        )
        
        # Initialize food to the child's own max_food
        child.food = child.max_food
        
        return child

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

    def __init__(self, x: float, y: float, generation: int=0) -> None:
        """Initialize a prey animal at the given position.
        
        Args:
            x: The initial x-coordinate.
            y: The initial y-coordinate.
        """
        super().__init__(x, y)
        
        # Evolutionary traits (can vary between individuals)
        self.speed = config.PREY_SPEED
        self.fear_distance = config.PREY_FEAR_DISTANCE
        self.mating_simulation = config.PREY_MATING_SIMULATION
        self.mating_search_distance = config.PREY_MATING_SEARCH_DISTANCE
        self.max_food = config.PREY_MAX_FOOD
        self.food_gain_per_grass = config.PREY_FOOD_GAIN_PER_GRASS
        self.starv_border = config.PREY_STARV_BORDER
        self.flee_energy_cost = config.PREY_FLEE_ENERGY_COST
        self.max_age = config.PREY_MAX_AGE
        self.high_age_health = config.PREY_HIGH_AGE_HEALTH
        
        self.food = self.max_food  # Initialize prey food
        self.is_fleeing = False
        self.is_eating = False
        self.grass_eaten = 0
        self.generation = generation  # Track generation for statistics
    
    def get_status(self) -> str:
        """Get a string describing the prey's current status.
        
        Returns:
            A string indicating the prey's state: 'Deceased', 'Fleeing',
            'Mating', 'Eating Grass', 'Starving', or 'Idle'.
        """
        if not self.alive:
            return "Deceased"
        if self.is_fleeing:
            return "Fleeing"
        if self.mating:
            return "Mating"
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
  
    def update(self, predator_hash: SpatialHash[Predator], prey_hash: SpatialHash[Prey], grass: GrassArray) -> None:
        """Update the prey's state for one simulation tick.
        
        Handles aging, fleeing from predators, mating behavior, energy consumption,
        movement towards areas with more grass, and eating grass to gain energy.
        
        Args:
            predator_hash: Spatial hash of all predators for fast proximity queries.
            prey_hash: Spatial hash of all prey for fast mating partner queries.
            grass: GrassArray for grass management.
        """
        # Reset status flags at the beginning of each update
        self.is_fleeing = False
        self.is_eating = False

        # check for death by age
        self.age += 1
        if self.age > self.max_age:
            if random.uniform(0, 1) > self.high_age_health:  # x% chance to die of old age
                self.alive = False
                config.prey_dead_by_age += 1
                return

        # Flee from predators using spatial hash (animal flees first, then the cost of moving is calculated)
        flee_dx = 0
        flee_dy = 0
        nearby_predators = predator_hash.get_nearby(self.x, self.y, self.fear_distance)
        for predator in nearby_predators:
            dx = self.x - predator.x
            dy = self.y - predator.y
            dist_sq = dx*dx + dy*dy
            if dist_sq < self.fear_distance**2 and dist_sq != 0:
                dist = dist_sq ** 0.5
                flee_dx += dx / dist
                flee_dy += dy / dist
        if flee_dx or flee_dy:
            norm = (flee_dx*flee_dx + flee_dy*flee_dy) ** 0.5 or 1
            self.x += (flee_dx / norm) * self.speed
            self.y += (flee_dy / norm) * self.speed
            self.is_fleeing = True # Set status flag
        else:
            self.x += random.uniform(-1, 1)
            self.y += random.uniform(-1, 1)
        
        # check for death by starvation
        if self.consumed_all_energy():  # Reduce food and possibly mark dead or starving
            self.alive = False
            config.prey_dead_by_starvation += 1
            return
        
        # Move towards areas with more grass (using direct array access for speed)
        chunk_i = int(self.x) // config.CHUNKSIZE
        chunk_j = int(self.y) // config.CHUNKSIZE
        
        if 0 <= chunk_i < grass.cols and 0 <= chunk_j < grass.rows:
            current_amount = grass.amounts[chunk_i, chunk_j]
            grass_dx, grass_dy = 0.0, 0.0
            
            # Look in a 3x3 grid using direct array access
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if i == 0 and j == 0:
                        continue
                    ni, nj = chunk_i + i, chunk_j + j
                    if 0 <= ni < grass.cols and 0 <= nj < grass.rows:
                        diff = grass.amounts[ni, nj] - current_amount
                        # Only add if neighbor has more grass
                        if diff > 0:
                            grass_dx += i * diff
                            grass_dy += j * diff
            
            if grass_dx != 0 or grass_dy != 0:
                norm = (grass_dx*grass_dx + grass_dy*grass_dy) ** 0.5 or 1
                # Scale the adjustment (using half of speed)
                self.x += (grass_dx / norm) * (self.speed * 0.5)
                self.y += (grass_dy / norm) * (self.speed * 0.5)
        
            # Boundary checks (use world size, not screen size)
            self.x = max(0, min(config.WORLD_WIDTH, self.x))
            self.y = max(0, min(config.WORLD_HEIGHT, self.y))
            
            # Recalculate chunk after movement
            chunk_i = int(self.x) // config.CHUNKSIZE
            chunk_j = int(self.y) // config.CHUNKSIZE
            
            # Consume grass and gain food based on current patch (direct array access)
            if 0 <= chunk_i < grass.cols and 0 <= chunk_j < grass.rows:
                grass_amount = grass.amounts[chunk_i, chunk_j]
                gain = grass_amount * self.food_gain_per_grass
                # Prey is eating if it gains food and is not full, and grass is available
                if gain > 0 and self.food < self.max_food and grass_amount > 0:
                    self.is_eating = True
                    self.grass_eaten += gain
                self.food = min(self.max_food, self.food + gain)
                # Track grass consumed for global total
                grass_consumed = min(1.0, grass_amount)  # Can't consume more than available
                grass.amounts[chunk_i, chunk_j] = max(0, grass_amount - 1)
                config.total_grass -= grass_consumed
        else:
            # Boundary checks if outside grass bounds
            self.x = max(0, min(config.WORLD_WIDTH, self.x))
            self.y = max(0, min(config.WORLD_HEIGHT, self.y))

        if not self.mating_simulation:
            # Simple reproduction: random chance each round
            self.reproduced = False  # Reset reproduction flag
            if random.random() / 4 < config.PREY_REPRODUCTION_RATE:
                self.reproduced = True
        else:
            # Complex mating simulation
            self.reproduced = False  # Reset reproduction flag
            
            # If currently mating, look for a partner (but not if fleeing - fleeing has priority)
            if self.mating and not self.is_fleeing:
                # Find nearby mating prey using spatial hash for efficiency
                nearby_prey = prey_hash.get_nearby(self.x, self.y, self.mating_search_distance)
                
                best_mate = None
                min_dist_sq = float('inf')
                
                for other in nearby_prey:
                    if other is self or not other.mating or not other.alive:
                        continue
                    dx = other.x - self.x
                    dy = other.y - self.y
                    dist_sq = dx*dx + dy*dy
                    if dist_sq < self.mating_search_distance**2 and dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        best_mate = other
                
                if best_mate:
                    # Check if close enough to mate
                    if min_dist_sq <= config.PREY_MATING_CLOSE_DISTANCE**2:
                        # Mating successful! One prey reproduces, both stop mating
                        self.reproduced = True
                        self.mating_partner = best_mate  # Store partner for trait inheritance
                        self.mating = False
                        best_mate.mating = False
                    else:
                        # Move towards the mate
                        dist = min_dist_sq ** 0.5 or 1
                        dx = best_mate.x - self.x
                        dy = best_mate.y - self.y
                        self.x += (dx / dist) * self.speed
                        self.y += (dy / dist) * self.speed
                        # Boundary checks after mating movement
                        self.x = max(0, min(config.WORLD_WIDTH, self.x))
                        self.y = max(0, min(config.WORLD_HEIGHT, self.y))
            
            # Random chance to enter mating mode (if not already mating)
            if not self.mating and random.random() < config.PREY_REPRODUCTION_RATE:
                self.mating = True

    def inherit_traits(self, partner: Prey) -> Prey:
        """Create a new prey with traits inherited from this prey and a partner.
        
        The child's trait value is calculated as:
        1. Random value between parent1's trait and parent2's trait
        2. Plus/minus a random mutation (±MUTATION_RATE * base_value from config)
        
        Using base values for mutation prevents multiplicative drift.
        
        Args:
            partner: The other parent prey.
            
        Returns:
            A new Prey with inherited traits.
        """
        child = Prey(self.x, self.y, generation=max(self.generation, partner.generation) + 1)
        
        # Helper function to inherit a trait with mutation
        def inherit_trait(p1_val: float, p2_val: float, base_val: float) -> float:
            # Random value between the two parents
            inherited = random.uniform(min(p1_val, p2_val), max(p1_val, p2_val))
            # Mutation: ±(MUTATION_RATE * base_value) to prevent multiplicative drift
            mutation = random.uniform(-config.MUTATION_RATE, config.MUTATION_RATE) * base_val
            return max(0.001, inherited + mutation)  # Ensure positive values
        
        # Inherit all evolutionary traits
        child.speed = inherit_trait(self.speed, partner.speed, config.PREY_SPEED)
        child.fear_distance = inherit_trait(
            self.fear_distance, partner.fear_distance, config.PREY_FEAR_DISTANCE
        )
        # mating_simulation is a boolean flag, inherit from random parent
        child.mating_simulation = random.choice([self.mating_simulation, partner.mating_simulation])
        child.mating_search_distance = inherit_trait(
            self.mating_search_distance, partner.mating_search_distance, 
            config.PREY_MATING_SEARCH_DISTANCE
        )
        child.max_food = inherit_trait(self.max_food, partner.max_food, config.PREY_MAX_FOOD)
        child.food_gain_per_grass = inherit_trait(
            self.food_gain_per_grass, partner.food_gain_per_grass, config.PREY_FOOD_GAIN_PER_GRASS
        )
        child.starv_border = inherit_trait(
            self.starv_border, partner.starv_border, config.PREY_STARV_BORDER
        )
        child.flee_energy_cost = inherit_trait(
            self.flee_energy_cost, partner.flee_energy_cost, config.PREY_FLEE_ENERGY_COST
        )
        child.max_age = inherit_trait(self.max_age, partner.max_age, config.PREY_MAX_AGE)
        child.high_age_health = min(1.0, inherit_trait(
            self.high_age_health, partner.high_age_health, config.PREY_HIGH_AGE_HEALTH
        ))  # Cap at 1.0 for probability
        
        # Initialize food to the child's own max_food
        child.food = child.max_food
        
        return child