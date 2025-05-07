# IMPORTS
import random
import pygame
import config                        # CONSTANTS
from animals import Predator, Prey   # Animal classes
from grass import Grass              # Grass class
from simulation import setup_simulation, update_simulation              # Simulation functions
from ui import draw_simulation, settings_menu, show_statistics_window   # UI functions

# MAIN 

def main():
    pygame.init()

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
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Handle click on Stop button
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                button_x = config.XLIM - config.BUTTON_X_OFFSET
                settings_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
                stop_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
                add_pred_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 2 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
                add_prey_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 3 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
                stats_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 4 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
                if settings_button_rect.collidepoint(mouse_pos):
                    action, new_settings = settings_menu(screen)
                    # Save new settings to global simulation parameters
                    config.PREY_MAX_FOOD = new_settings["Prey Health"]
                    config.PREDATOR_MAX_FOOD = new_settings["Predator Health"]
                    config.PREY_REPRODUCTION_RATE = new_settings["Prey Reproduction Rate"]
                    config.PREDATOR_REPRODUCTION_RATE = new_settings["Predator Reproduction Rate"]
                    config.GRASS_GROWTH_RATE = new_settings["Grass Growth Rate"]
                    config.GRASS_MAX_AMOUNT = new_settings["Max Grass per Field"]
                    config.PREY_FEAR_DISTANCE = new_settings["Prey Fear Distance"]
                    config.PREY_SPEED = new_settings["Prey Speed"]
                    config.PREDATOR_SPEED = new_settings["Predator Speed"]
                    
                    if action == "restart":
                        predators, preys, grass = setup_simulation()
                    elif action == "resume":
                        # Continue with updated settings
                        pass
                elif stop_button_rect.collidepoint(mouse_pos):
                    running = False
                elif add_pred_button_rect.collidepoint(mouse_pos):
                    predators.append(Predator(random.uniform(0, config.XLIM), random.uniform(0, config.YLIM)))
                elif add_prey_button_rect.collidepoint(mouse_pos):
                    preys.append(Prey(random.uniform(0, config.XLIM), random.uniform(0, config.YLIM)))
                # NEW: Handle click on Statistics button
                elif stats_button_rect.collidepoint(mouse_pos):
                    show_statistics_window(predators, preys, grass)

        # Calculate simulation step
        update_simulation(predators, preys, grass)
        # Render simulation state only after update
        draw_simulation(screen, predators, preys, grass)
        clock.tick(config.FPS)  # 30 FPS

    pygame.quit()

if __name__ == "__main__":
    main()
