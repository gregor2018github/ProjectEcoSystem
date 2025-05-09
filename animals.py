from abc import ABC, abstractmethod
import pygame
import random
import config

# Animal class definitions
class Animal(ABC):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True
        self.starving = False  # attribute to track starvation
        self.killed = False  # attribute to track kill events
        self.age = 0  

    def get_rect(self):
        # SIZE must be defined in subclasses
        return pygame.Rect(self.x - self.SIZE, self.y - self.SIZE, 2 * self.SIZE, 2 * self.SIZE)

    @abstractmethod
    def get_status(self):
        """Returns a string describing the animal's current status."""
        pass

    def consumed_all_energy(self):
        """
        Check if the animal has consumed all its energy, returns true in case.
        If the animal is not dead, check if it is starving. 
        Consider the animal type (Predator or Prey) and its state (hunting or not). 
        """
        if isinstance(self, Predator):
            # Predator energy consumption logic
            if self.hunting:
                self.food -= config.PREDATOR_HUNTING_ENERGY_COST
            else:
                self.food -= config.PREDATOR_REGULAR_ENERGY_COST
        else:
            # Prey energy consumption logic
            self.food -= 1
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
    def update(self, animals, grass):
        pass

    @abstractmethod
    def draw(self, screen):
        pass

class Predator(Animal):
    COLOR = (255, 0, 0)  # Red
    SIZE = 5

    def __init__(self, x, y):
        super().__init__(x, y)
        self.food = config.PREDATOR_MAX_FOOD  # Initialize predator food
        self.hunting = False  # attribute to track hunting state
        self.avoiding_predator_flag = False # For status display

    def get_status(self):
        if not self.alive:
            return "Deceased"
        if self.hunting:
            return "Hunting"
        if self.avoiding_predator_flag:
            return "Avoiding Predator"
        if self.starving:
            return "Starving"
        return "Idle"
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.COLOR, (int(self.x), int(self.y)), self.SIZE)
    
    def update(self, animals, grass):
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
            for other in animals:
                if isinstance(other, Predator) and other != self:
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
            # Find the closest prey only if not avoiding other predators
            for prey in animals:
                # Ensure we are only targeting Prey
                if isinstance(prey, Prey): 
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
                    config.prey_dead_by_hunting += 1
                    # Add food gain on kill; cap to max
                    self.food = min(config.PREDATOR_MAX_FOOD, self.food + config.PREDATOR_FOOD_GAIN_PER_KILL)
            # if not hunting, move randomly
            else:
                self.hunting = False
                self.x += random.uniform(-1, 1)
                self.y += random.uniform(-1, 1)

        # Boundary checks and energy consumption
        self.x = max(0, min(config.XLIM, self.x))
        self.y = max(0, min(config.YLIM, self.y))
        
class Prey(Animal):
    COLOR = (255, 255, 255)  # Blue
    SIZE = 3

    def __init__(self, x, y):
        super().__init__(x, y)
        self.food = config.PREY_MAX_FOOD  # Initialize prey food
        self.is_fleeing = False
        self.is_eating = False
    
    def get_status(self):
        if not self.alive:
            return "Deceased"
        if self.is_fleeing:
            return "Fleeing"
        if self.is_eating: # Eating takes precedence over starving if both are true
            return "Eating Grass"
        if self.starving:
            return "Starving"
        return "Idle"

    def draw(self, screen):
        pygame.draw.circle(screen, self.COLOR, (int(self.x), int(self.y)), self.SIZE)
  
    def update(self, animals, grass):
        # Reset status flags at the beginning of each update
        self.is_fleeing = False
        self.is_eating = False

        # check for death by age
        self.age += 1
        if self.age > config.PREY_MAX_AGE:
            self.alive = False
            config.prey_dead_by_age += 1
            return
        # check for death by starvation
        if self.consumed_all_energy():  # Reduce food and possibly mark dead or starving
            self.alive = False
            config.prey_dead_by_starvation += 1
            return

        # Flee from predators
        flee_dx = 0
        flee_dy = 0
        for predator in animals:
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
        
        self.x = max(0, min(config.XLIM, self.x))
        self.y = max(0, min(config.YLIM, self.y))
        # Consume grass and gain food based on current patch
        if chunk in grass:
            gain = grass[chunk].amount * config.PREY_FOOD_GAIN_PER_GRASS
            # Prey is eating if it gains food and is not full, and grass is available
            if gain > 0 and self.food < config.PREY_MAX_FOOD and grass[chunk].amount > 0:
                self.is_eating = True
            self.food = min(config.PREY_MAX_FOOD, self.food + gain)
            grass[chunk].amount = max(0, grass[chunk].amount - 1)

