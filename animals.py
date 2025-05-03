from abc import ABC, abstractmethod
import pygame
import random
from config import *

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
        self.food = PREDATOR_MAX_FOOD  # Initialize predator food
        self.killed = False  # attribute to track kill events
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.COLOR, (int(self.x), int(self.y)), self.SIZE)
    
    def update(self, animals, grass):
        self.killed = False
        target = None
        min_dist = float('inf')
        for prey in animals:
            dx = prey.x - self.x
            dy = prey.y - self.y
            dist = (dx**2 + dy**2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                target = prey
        if target:
            dx = target.x - self.x
            dy = target.y - self.y
            dist = (dx**2 + dy**2) ** 0.5 or 1
            self.x += (dx / dist) * PREDATOR_SPEED
            self.y += (dy / dist) * PREDATOR_SPEED
            if min_dist < self.SIZE + target.SIZE and target.alive:
                target.alive = False
                self.killed = True  # Mark kill for reproduction
                # Add food gain on kill; cap to max
                self.food = min(PREDATOR_MAX_FOOD, self.food + PREDATOR_FOOD_GAIN_PER_KILL)
        self.x = max(0, min(XLIM, self.x))
        self.y = max(0, min(YLIM, self.y))
        self.consume_energy()  # Reduce food and possibly mark dead

class Prey(Animal):
    COLOR = (255, 255, 255)  # Blue
    SIZE = 3

    def __init__(self, x, y):
        super().__init__(x, y)
        self.food = PREY_MAX_FOOD  # Initialize prey food
    
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
            if dist < PREY_FEAR_DISTANCE and dist != 0:
                flee_dx += dx / dist
                flee_dy += dy / dist
        if flee_dx or flee_dy:
            norm = (flee_dx**2 + flee_dy**2) ** 0.5 or 1
            self.x += (flee_dx / norm) * PREY_SPEED
            self.y += (flee_dy / norm) * PREY_SPEED
        else:
            self.x += random.uniform(-1, 1)
            self.y += random.uniform(-1, 1)
        
        # Move away from areas with little grass
        chunk = (int(self.x) // CHUNKSIZE, int(self.y) // CHUNKSIZE)
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
                self.x += (grass_dx / norm) * (PREY_SPEED * 0.5)
                self.y += (grass_dy / norm) * (PREY_SPEED * 0.5)
        
        self.x = max(0, min(XLIM, self.x))
        self.y = max(0, min(YLIM, self.y))
        # Consume grass and gain food based on current patch
        if chunk in grass:
            gain = grass[chunk].amount * PREY_FOOD_GAIN_PER_GRASS
            self.food = min(PREY_MAX_FOOD, self.food + gain)
            grass[chunk].amount = max(0, grass[chunk].amount - 1)
        self.consume_energy()  # Reduce food and possibly mark dead