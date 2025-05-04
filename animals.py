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
        # Food to be initialized by child classes

    def consume_energy(self):
        self.food -= 1
        if self.food <= 0:
            self.alive = False

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
        self.starving = False  # attribute to track starvation
        self.killed = False  # attribute to track kill events
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.COLOR, (int(self.x), int(self.y)), self.SIZE)
    
    def update(self, animals, grass):
        self.killed = False
        target = None
        min_dist_prey = float('inf')
        avoid_dx = 0
        avoid_dy = 0
        predator_too_close = False

        # Separate loops for finding prey and checking for nearby predators
        
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
            norm = (avoid_dx**2 + avoid_dy**2)**0.5 or 1 # Normalize the total avoidance vector
            self.x += (avoid_dx / norm) * config.PREDATOR_SPEED 
            self.y += (avoid_dy / norm) * config.PREDATOR_SPEED
            # print("Predator avoiding another predator") # Optional: keep for debugging
        else:
            # Find the closest prey only if not avoiding other predators
            for prey in animals:
                # Ensure we are only targeting Prey
                if isinstance(prey, Prey) and prey.alive: 
                    dx = prey.x - self.x
                    dy = prey.y - self.y
                    dist = (dx**2 + dy**2)**0.5
                    if dist < min_dist_prey:
                        min_dist_prey = dist
                        target = prey

            # If a target is found, move towards it
            if target:
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
                    # Add food gain on kill; cap to max
                    self.food = min(config.PREDATOR_MAX_FOOD, self.food + config.PREDATOR_FOOD_GAIN_PER_KILL)

        # Boundary checks and energy consumption
        self.x = max(0, min(config.XLIM, self.x))
        self.y = max(0, min(config.YLIM, self.y))
        self.consume_energy()  # Reduce food and possibly mark dead
        if self.food < config.PREDATOR_STARV_BORDER * config.PREDATOR_MAX_FOOD:
            self.starving = True
        else:
            self.starving = False

class Prey(Animal):
    COLOR = (255, 255, 255)  # Blue
    SIZE = 3

    def __init__(self, x, y):
        super().__init__(x, y)
        self.food = config.PREY_MAX_FOOD  # Initialize prey food
        self.starving = False  # attribute to track starvation
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.COLOR, (int(self.x), int(self.y)), self.SIZE)
  
    def update(self, animals, grass):
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
            self.food = min(config.PREY_MAX_FOOD, self.food + gain)
            grass[chunk].amount = max(0, grass[chunk].amount - 1)
        self.consume_energy()  # Reduce food and possibly mark dead
        if self.food < config.PREY_STARV_BORDER * config.PREY_MAX_FOOD:
            self.starving = True
        else:
            self.starving = False