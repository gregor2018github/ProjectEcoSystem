# IMPORTS
import pygame
import config                        # CONSTANTS
from animals import Predator, Prey   # Animal classes
from grass import Grass              # Grass class
from simulation import setup_simulation, update_simulation              # Simulation functions
from ui import draw_simulation       # UI function
from event_handler import process_event, initialize_sounds  # Event handling function

# MAIN 

def main():
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

    screen = pygame.display.set_mode((config.XLIM, config.YLIM))
    clock = pygame.time.Clock()
    predators, preys, grass = setup_simulation()

    running = True
    stopped = False
    hover_animal = None # Stores the animal currently being hovered over
    current_mouse_pos = (0, 0) # Stores the current mouse position for hover window
    locked_animal = None # Stores the animal whose info window is locked

    while running:
        current_mouse_pos = pygame.mouse.get_pos() # Get current mouse position once per frame
        all_animals_for_hover = predators + preys # Update animal list each frame for hover/click checks

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
