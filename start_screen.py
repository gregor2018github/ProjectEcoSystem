"""
Start Screen Module for Project Ecosystem

This module displays a start screen with configuration options before the simulation begins.
Users can select world size, FPS, and starting populations for prey and predators.
"""

import pygame
import sys
from typing import Dict, Any, Tuple, List, Optional

# Constants for start screen
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BACKGROUND_COLOR = (20, 40, 20)

# UI Element dimensions and positions
TITLE_FONT_SIZE = 72
TITLE_Y = 60

DROPDOWN_WIDTH = 160
DROPDOWN_HEIGHT = 40
DROPDOWN_FONT_SIZE = 22
DROPDOWN_SPACING = 220
DROPDOWN_START_X = 450
DROPDOWN_ROW1_Y = 180
DROPDOWN_ROW2_Y = 280

BUTTON_WIDTH = 410
BUTTON_HEIGHT = 70
BUTTON_X = (SCREEN_WIDTH - BUTTON_WIDTH) // 2
BUTTON_Y = 380
BUTTON_FONT_SIZE = 36

# Colors
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (60, 80, 70)
LIGHT_GRAY = (140, 160, 150)
GREEN = (80, 120, 90)
LIGHT_GREEN = (100, 140, 110)
DROPDOWN_BG = (70, 100, 85)
DROPDOWN_HOVER = (90, 120, 105)

# Dropdown arrow
ARROW_SIZE = 10


class Dropdown:
    """A dropdown menu UI element for selecting values."""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 label: str, options: List[Any], default_value: Any):
        """Initialize a dropdown menu.
        
        Args:
            x: X position of the dropdown
            y: Y position of the dropdown
            width: Width of the dropdown
            height: Height of the dropdown
            label: Label text to display
            options: List of selectable options
            default_value: Default selected value
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.options = options
        self.selected = default_value
        self.is_open = False
        self.hover_option = None
        
        # Create rects for dropdown options
        self.option_rects = []
        for i, option in enumerate(options):
            option_rect = pygame.Rect(x, y + height + i * height, width, height)
            self.option_rects.append(option_rect)
    
    def draw(self, screen: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        """Draw the dropdown menu.
        
        Args:
            screen: Pygame surface to draw on
            font: Font for the selected value
            small_font: Font for the label text
        """
        # Draw label
        label_surface = small_font.render(self.label, True, WHITE)
        label_rect = label_surface.get_rect(midbottom=(self.rect.centerx, self.rect.top - 5))
        screen.blit(label_surface, label_rect)
        
        # Draw main dropdown box
        color = DROPDOWN_HOVER if self.rect.collidepoint(pygame.mouse.get_pos()) else DROPDOWN_BG
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, LIGHT_GRAY, self.rect, 2, border_radius=5)
        
        # Draw selected value
        value_text = str(self.selected)
        value_surface = font.render(value_text, True, WHITE)
        value_rect = value_surface.get_rect(center=(self.rect.centerx, self.rect.centery))
        screen.blit(value_surface, value_rect)
        
        # Draw dropdown arrow
        arrow_x = self.rect.right - 25
        arrow_y = self.rect.centery
        if self.is_open:
            # Up arrow
            points = [
                (arrow_x, arrow_y - ARROW_SIZE // 2),
                (arrow_x - ARROW_SIZE, arrow_y + ARROW_SIZE // 2),
                (arrow_x + ARROW_SIZE, arrow_y + ARROW_SIZE // 2)
            ]
        else:
            # Down arrow
            points = [
                (arrow_x, arrow_y + ARROW_SIZE // 2),
                (arrow_x - ARROW_SIZE, arrow_y - ARROW_SIZE // 2),
                (arrow_x + ARROW_SIZE, arrow_y - ARROW_SIZE // 2)
            ]
        pygame.draw.polygon(screen, WHITE, points)
        
        # Draw dropdown options if open
        if self.is_open:
            for i, (option, option_rect) in enumerate(zip(self.options, self.option_rects)):
                # Highlight hovered option
                if option == self.hover_option:
                    color = DROPDOWN_HOVER
                else:
                    color = DROPDOWN_BG
                
                pygame.draw.rect(screen, color, option_rect, border_radius=5)
                pygame.draw.rect(screen, LIGHT_GRAY, option_rect, 2, border_radius=5)
                
                option_text = str(option)
                option_surface = font.render(option_text, True, WHITE)
                option_text_rect = option_surface.get_rect(center=option_rect.center)
                screen.blit(option_surface, option_text_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events for the dropdown.
        
        Args:
            event: Pygame event to handle
            
        Returns:
            True if event was handled, False otherwise
        """
        if event.type == pygame.MOUSEMOTION:
            if self.is_open:
                self.hover_option = None
                for option, option_rect in zip(self.options, self.option_rects):
                    if option_rect.collidepoint(event.pos):
                        self.hover_option = option
                        break
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check if clicked on main dropdown
                if self.rect.collidepoint(event.pos):
                    self.is_open = not self.is_open
                    return True
                
                # Check if clicked on an option
                if self.is_open:
                    for option, option_rect in zip(self.options, self.option_rects):
                        if option_rect.collidepoint(event.pos):
                            self.selected = option
                            self.is_open = False
                            return True
                    
                    # Clicked outside dropdown, close it
                    self.is_open = False
                    return True
        
        return False
    
    def get_value(self) -> Any:
        """Get the currently selected value."""
        return self.selected


class Button:
    """A clickable button UI element."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str):
        """Initialize a button.
        
        Args:
            x: X position of the button
            y: Y position of the button
            width: Width of the button
            height: Height of the button
            text: Text to display on the button
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
    
    def draw(self, screen: pygame.Surface, font: pygame.font.Font, enabled: bool = True) -> None:
        """Draw the button.
        
        Args:
            screen: Pygame surface to draw on
            font: Font for the button text
            enabled: Whether the button is active and can be hovered
        """
        # Update hover state
        self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos()) if enabled else False
        
        # Draw button
        color = LIGHT_GREEN if self.is_hovered else GREEN
        if not enabled:
            # Dim the button if disabled
            color = (color[0] // 2, color[1] // 2, color[2] // 2)
            
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE if enabled else GRAY, self.rect, 3, border_radius=8)
        
        # Draw text
        text_surface = font.render(self.text, True, WHITE if enabled else GRAY)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def is_clicked(self, event: pygame.event.Event) -> bool:
        """Check if the button was clicked.
        
        Args:
            event: Pygame event to check
            
        Returns:
            True if button was clicked, False otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


def show_start_screen() -> Dict[str, Any]:
    """Display the start screen and return the selected configuration.
    
    Returns:
        Dictionary containing the selected configuration values:
        - WORLD_SIZE_MULTIPLIER: float
        - FPS: int
        - NUM_PREYS: int
        - NUM_PREDATORS: int
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Project Ecosystem - Start Screen")
    clock = pygame.time.Clock()
    
    # Load background image
    try:
        background = pygame.image.load("assets/start_screen_background.png")
        background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except:
        # Fallback to solid color if image not found
        background = None
    
    # Fonts
    title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
    button_font = pygame.font.Font(None, BUTTON_FONT_SIZE)
    dropdown_font = pygame.font.Font(None, DROPDOWN_FONT_SIZE)
    label_font = pygame.font.Font(None, 24)
    
    # Create dropdowns
    size_dropdown = Dropdown(
        DROPDOWN_START_X, DROPDOWN_ROW1_Y, DROPDOWN_WIDTH, DROPDOWN_HEIGHT,
        "Gamefield Size:", [1.0, 1.5, 2.0, 3.0], 2.0
    )
    
    fps_dropdown = Dropdown(
        DROPDOWN_START_X + DROPDOWN_SPACING, DROPDOWN_ROW1_Y, DROPDOWN_WIDTH, DROPDOWN_HEIGHT,
        "Max FPS:", [30, 45, 60, 120], 120
    )
    
    prey_dropdown = Dropdown(
        DROPDOWN_START_X, DROPDOWN_ROW2_Y, DROPDOWN_WIDTH, DROPDOWN_HEIGHT,
        "Prey Count Start:", [5, 20, 30, 55, 100, 200], 100
    )
    
    pred_dropdown = Dropdown(
        DROPDOWN_START_X + DROPDOWN_SPACING, DROPDOWN_ROW2_Y, DROPDOWN_WIDTH, DROPDOWN_HEIGHT,
        "Predator Count Start:", [0, 4, 5, 10, 25], 10
    )
    
    dropdowns = [size_dropdown, fps_dropdown, prey_dropdown, pred_dropdown]
    
    # Create start button
    start_button = Button(BUTTON_X, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT, "Start Simulation")
    
    running = True
    while running:
        # Check if any dropdown is open
        any_dropdown_open = any(d.is_open for d in dropdowns)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Handle dropdown events
            event_handled = False
            
            # If clicking to open a new dropdown, close all others first to allow one-click switching
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for dropdown in dropdowns:
                    if dropdown.rect.collidepoint(event.pos) and not dropdown.is_open:
                        for d in dropdowns:
                            d.is_open = False
                        break
            
            for dropdown in dropdowns:
                if dropdown.handle_event(event):
                    event_handled = True
                    break # Only one dropdown handles an event at a time
            
            if event_handled:
                continue
                
            # Handle button click (only if no dropdown is open)
            if not any_dropdown_open and start_button.is_clicked(event):
                # Return selected configuration
                return {
                    "WORLD_SIZE_MULTIPLIER": size_dropdown.get_value(),
                    "FPS": fps_dropdown.get_value(),
                    "NUM_PREYS": prey_dropdown.get_value(),
                    "NUM_PREDATORS": pred_dropdown.get_value()
                }
        
        # Draw everything
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BACKGROUND_COLOR)
        
        # Draw title
        title_surface = title_font.render("Project Ecosystem", True, WHITE)
        title_rect = title_surface.get_rect(centerx=SCREEN_WIDTH // 2, y=TITLE_Y)
        screen.blit(title_surface, title_rect)
        
        # Draw start button
        start_button.draw(screen, button_font, enabled=not any_dropdown_open)
        
        # Draw dropdowns
        # Draw closed dropdowns first, then open one to ensure it's on top
        for dropdown in dropdowns:
            if not dropdown.is_open:
                dropdown.draw(screen, dropdown_font, label_font)
        for dropdown in dropdowns:
            if dropdown.is_open:
                dropdown.draw(screen, dropdown_font, label_font)
        
        pygame.display.flip()
        clock.tick(60)
    
    # Should not reach here, but return defaults if loop exits
    return {
        "WORLD_SIZE_MULTIPLIER": 2.0,
        "FPS": 120,
        "NUM_PREYS": 55,
        "NUM_PREDATORS": 5
    }


if __name__ == "__main__":
    # Test the start screen
    config = show_start_screen()
    print("Selected configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
