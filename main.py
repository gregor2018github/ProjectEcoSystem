# IMPORTS
import pygame
import config                        # CONSTANTS
from animals import Predator, Prey   # Animal classes
from grass import Grass              # Grass class
from simulation import setup_simulation, update_simulation              # Simulation functions
from ui import draw_simulation, settings_menu, show_statistics_window   # UI functions
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
    while running:
        for event in pygame.event.get():
            running, stopped, predators, preys, grass = process_event(
                event, predators, preys, grass, screen, running, stopped
            )

        # Calculate simulation step
        if not stopped:
            # Update simulation state
            update_simulation(predators, preys, grass)
            # Render simulation state only after update
            draw_simulation(screen, predators, preys, grass)
        clock.tick(config.FPS)  # 30 FPS

    pygame.quit()

if __name__ == "__main__":
    main()
