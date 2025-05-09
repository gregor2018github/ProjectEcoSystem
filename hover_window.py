import pygame
import config
from animals import Predator, Prey # Import specific animal classes for isinstance checks

class HoverWindow:
    def __init__(self, animal, anchor_pos): # Changed mouse_pos to anchor_pos
        self.animal = animal
        self.anchor_pos = anchor_pos # Store the anchor position
        self.font = pygame.font.Font(None, 20) # Small font for the hover info
        self.padding = 5
        self.line_height = 20
        self.window_color = (40, 40, 40, 210) # Semi-transparent dark background
        self.text_color = (230, 230, 230)     # Light grey text

        # Prepare text lines
        self.lines = []
        self.lines.append(f"Type: {animal.__class__.__name__}")
        
        max_age_key = config.PREDATOR_MAX_AGE if isinstance(animal, Predator) else config.PREY_MAX_AGE
        self.lines.append(f"Age: {animal.age} / {max_age_key}")
        
        max_food_key = config.PREDATOR_MAX_FOOD if isinstance(animal, Predator) else config.PREY_MAX_FOOD
        self.lines.append(f"Food: {animal.food:.1f} / {max_food_key}")
        
        status = animal.get_status()
        self.lines.append(f"Status: {status}")

        if isinstance(animal, Predator):
            self.lines.append(f"Prey Eaten: {animal.prey_eaten}")
        elif isinstance(animal, Prey):
            self.lines.append(f"Grass Eaten: {round(animal.grass_eaten, 0)}")
        
        starvation_bool = animal.starving
        self.lines.append(f"Starving: " + ("Yes" if starvation_bool else "No"))


        self.lines.append(f"Position: ({int(animal.x)}, {int(animal.y)})")


        # Calculate window size based on content
        self.max_line_width = 0
        for line_text in self.lines:
            text_surface = self.font.render(line_text, True, self.text_color)
            if text_surface.get_width() > self.max_line_width:
                self.max_line_width = text_surface.get_width()
        
        self.width = self.max_line_width + 2 * self.padding
        self.height = len(self.lines) * self.line_height + (len(self.lines) -1) * (self.padding // 2) + 2 * self.padding


        # Position the window near the anchor_pos, trying to keep it on screen
        x = self.anchor_pos[0] + 15 # Offset from anchor
        y = self.anchor_pos[1] + 15

        if x + self.width > config.XLIM: # If goes off right edge
            x = self.anchor_pos[0] - self.width - 15
        if y + self.height > config.YLIM: # If goes off bottom edge
            y = self.anchor_pos[1] - self.height - 15
        
        self.rect = pygame.Rect(x, y, self.width, self.height)

    def draw(self, screen):
        # Create a surface with per-pixel alpha for transparency
        temp_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        temp_surface.fill(self.window_color) # Apply background color with alpha
        
        # Draw text lines onto the temporary surface
        current_y = self.padding
        for line_text in self.lines:
            text_surface = self.font.render(line_text, True, self.text_color)
            temp_surface.blit(text_surface, (self.padding, current_y))
            current_y += self.line_height + (self.padding // 2) 
            
        screen.blit(temp_surface, self.rect.topleft)
