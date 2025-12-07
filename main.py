###############################################
# Imports
###############################################

from __future__ import annotations
import pygame
import config                        # CONSTANTS
from animals import Predator, Prey, Animal   # Animal classes
from grass import Grass              # Grass class
from simulation import setup_simulation, update_simulation              # Simulation functions
from ui import draw_simulation       # UI function
from event_handler import process_event, initialize_sounds  # Event handling function

###############################################
# Main
############################################### 

def main() -> None:
    """Main entry point for the ecosystem simulation.
    
    Initializes pygame, sets up the simulation, and runs the main game loop.
    Handles events, updates simulation state when not paused, and renders
    each frame. Supports camera movement with WASD and arrow keys.
    """
    pygame.init()
    initialize_sounds()

    # set the size of the game field, either by locked values or by display size
    if not config.LOCKED_SCREEN_SIZE:
        # Get user's display info and compute window dimensions
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        config.XLIM = screen_width
        config.YLIM = screen_height
    
    # Calculate world size based on screen size (2x width and 2x height = 4x area)
    config.WORLD_WIDTH = config.XLIM * config.WORLD_SIZE_MULTIPLIER
    config.WORLD_HEIGHT = config.YLIM * config.WORLD_SIZE_MULTIPLIER
    
    # Initialize camera position (start at top-left)
    config.camera_x = 0.0
    config.camera_y = 0.0

    screen = pygame.display.set_mode((config.XLIM, config.YLIM))
    clock = pygame.time.Clock()
    predators, preys, grass = setup_simulation()

    running = True
    stopped = False
    hover_animal = None # Stores the animal currently being hovered over
    current_mouse_pos = (0, 0) # Stores the current mouse position for hover window
    locked_animal = None # Stores the animal whose info window is locked
    
    # FPS counter variables (lightweight, updates every 2 seconds)
    fps_frame_count = 0
    fps_timer = 0.0

    while running:
        # Track frame time for FPS calculation
        dt = clock.get_time() / 1000.0  # Delta time in seconds
        fps_frame_count += 1
        fps_timer += dt
        
        # Update displayed FPS every 2 seconds
        if fps_timer >= config.FPS_UPDATE_INTERVAL:
            config.current_fps = fps_frame_count / fps_timer
            fps_frame_count = 0
            fps_timer = 0.0
        
        current_mouse_pos = pygame.mouse.get_pos() # Get current mouse position once per frame
        all_animals_for_hover = predators + preys # Update animal list each frame for hover/click checks
        
        # Handle continuous key presses for camera movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            config.camera_y = max(0, config.camera_y - config.CAMERA_SPEED)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            config.camera_y = min(config.WORLD_HEIGHT - config.YLIM, config.camera_y + config.CAMERA_SPEED)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            config.camera_x = max(0, config.camera_x - config.CAMERA_SPEED)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            config.camera_x = min(config.WORLD_WIDTH - config.XLIM, config.camera_x + config.CAMERA_SPEED)

        for event in pygame.event.get():
            # Pass event to handler, which might consume it (e.g., button click)
            # and now also handles hover and lock logic
            running, stopped, predators, preys, grass, _, hover_animal, locked_animal = process_event(
                event, predators, preys, grass, screen, running, stopped,
                hover_animal, locked_animal, all_animals_for_hover
            )
            # The underscore '_' is used for event_handled_by_button_action as it's not directly used in main loop after this call.
            # Its effect is contained within process_event (e.g., preventing animal lock on button click).

        # Update simulation state if not stopped
        if not stopped:
            update_simulation(predators, preys, grass)
        
        # Always render the simulation state (including hover window)
        # Pass hover_animal, current_mouse_pos (for general hover), and locked_animal
        draw_simulation(screen, predators, preys, grass, hover_animal, current_mouse_pos, locked_animal)
            
        clock.tick(config.FPS)  # 30 FPS

    pygame.quit()

if __name__ == "__main__":
    main()
